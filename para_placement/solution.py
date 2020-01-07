import copy

from pulp import *

from para_placement.config import DC
from para_placement.evaluation import *
from para_placement.model import *
from para_placement.cg import generate_configurations_dc, generate_configuration_greedy_dc_dfs
from progress.bar import PixelBar
from ttictoc import TicToc


def linear_programming(model: Model) -> (float, int, float, float):
    print("\n>>> Start LP <<<")
    problem = LpProblem("VNF Placement", LpMaximize)

    # config.K = max(config.K / 2, 10)
    with TicToc("GeneratingConfiguration"), PixelBar(">> Generating configuration set for SFC") as bar:
        bar.max = len(model.sfc_list)
        for idx, sfc in enumerate(model.sfc_list):
            sfc.configurations = generate_configurations_dc(model.topo, sfc)

            # filter configurations whose latency is legal. IMPORTANT
            sfc.configurations = list(
                filter(lambda c: c.get_latency() <= sfc.latency, sfc.configurations))

            for configuration in sfc.configurations:
                configuration.var = LpVariable(
                    configuration.name, 0, 1, LpContinuous)

            bar.next()

    # total number of valid sfc
    config_num = sum(len(sfc.configurations) for sfc in model.sfc_list)
    valid_sfc_num = sum(len(sfc.configurations) > 0 for sfc in model.sfc_list)
    print("Number of LP Variables: {}\tValid SFC: {}".format(
        config_num, valid_sfc_num))

    # Objective function
    with TicToc("OBJ"):
        problem += lpSum((configuration.var for configuration in sfc.configurations)
                         for sfc in model.sfc_list), "Total number of accepted requests"

    # Constraints
    with TicToc("SBJ Basic"):
        # basic constraints
        for sfc in model.sfc_list:
            problem += lpSum(
                configuration.var for configuration in sfc.configurations) <= 1.0, "Basic_{}".format(sfc.idx)

    # computing resource constraints
    with TicToc("SBJ CP"):
        for index, info in model.topo.nodes.data():
            problem += lpSum(configuration.var * configuration.computing_resource[index]
                             for sfc in model.sfc_list
                             for configuration in sfc.configurations
                             if index in configuration.computing_resource) <= info['computing_resource'], "CR_{}".format(index)

    # throughput constraints
    with TicToc("SBJ TP"):
        for start, end, info in model.topo.edges.data():
            problem += lpSum(configuration.var * sfc.throughput * configuration.edges[(start, end)]
                             for sfc in model.sfc_list
                             for configuration in sfc.configurations
                             if (start, end) in configuration.edges) <= info['bandwidth'], "TP_{}_{}".format(start, end)

    with TicToc("LP Solving"):
        problem.solve()

    # reduce the configurations for each sfc
    for sfc in model.sfc_list:
        sfc.configurations = list(
            filter(lambda c: c.var.varValue > 0, sfc.configurations))

    obj_val = value(problem.objective)
    accept_sfc_number = sum(len(sfc.configurations) >
                            0 for sfc in model.sfc_list)
    latency = 0
    if accept_sfc_number is not 0:
        latency = sum(
            configuration.get_latency() * configuration.var.varValue for sfc in model.sfc_list for configuration in
            sfc.configurations) / accept_sfc_number
    print("Objective Value: {}({}, {}ms)".format(
        obj_val, accept_sfc_number, latency))

    return obj_val, accept_sfc_number, latency, model.compute_resource_utilization()


def rounding_one(model: Model):
    """
    Rounding method: x < 1.0 => x = 0
                     x == 1.0 => x = 1.0
    :param model:
    :return:
    """
    print(">> One Rounding <<")

    sfc_list = list(filter(lambda s: len(
        s.configurations) > 0, model.sfc_list))

    for sfc in sfc_list:
        for configuration in sfc.configurations:
            if configuration.var.varValue == 1:
                sfc.accepted_configuration = configuration
                if not evaluate(model):
                    sfc.accepted_configuration = None
                break

    if not model.get_accepted_sfc_list():
        rounding_greedy(model)
        # rounding_randomized(model)


def rounding_randomized(model: Model):
    print(">> Randomized Rounding <<")
    sfc_list = list(filter(lambda s: len(
        s.configurations) > 0, model.sfc_list))

    for sfc in sfc_list:
        for configuration in sfc.configurations:
            prob = random.random()
            if prob < configuration.var.varValue:
                sfc.accepted_configuration = configuration
                if evaluate(model):
                    break
                else:
                    sfc.accepted_configuration = None


def rounding_greedy(model: Model):
    """
    Rounding method:
    1. SFCs are sorted by resource usage ratio
    2. Configurations are sorted by its var value
    3. Traverse and choose the available configuration
    :param model:
    :return:
    """
    print(">> Greedy Rounding <<")
    sfc_list = list(filter(lambda s: len(
        s.configurations) > 0, model.sfc_list))

    for sfc in sfc_list:
        # varValue, latency, cr ratio
        sfc.configurations.sort(key=lambda c: c.var.varValue, reverse=True)

    # sfc sorted by computing resource ratio
    sfc_list.sort(
        key=lambda s: s.configurations[0].computing_resource_ratio(model.topo))

    for sfc in sfc_list:
        for configuration in sfc.configurations:
            sfc.accepted_configuration = configuration
            if evaluate(model):
                break
            else:
                sfc.accepted_configuration = None

    if not model.get_accepted_sfc_list():
        greedy_dc(model)


# recursively
def rounding_to_integral(model: Model, rounding_method=rounding_greedy) -> (float, int, float, float):
    print("\n>>> Start Rounding <<<")

    rounding_method(model)

    accepted_sfc_list = model.get_accepted_sfc_list()

    sub_model = Model(copy.deepcopy(model.topo), [
                      sfc for sfc in model.sfc_list if sfc.accepted_configuration is None])
    # computing resource reduction
    for index, info in sub_model.topo.nodes.data():
        info['computing_resource'] -= sum(sfc.accepted_configuration.computing_resource[index]
                                          for sfc in accepted_sfc_list
                                          if index in sfc.accepted_configuration.computing_resource)
    # throughput reduction
    for start, end, info in sub_model.topo.edges.data():
        info['bandwidth'] -= sum(sfc.throughput * sfc.accepted_configuration.edges[(start, end)]
                                 for sfc in accepted_sfc_list
                                 if (start, end) in sfc.accepted_configuration.edges)

    if accepted_sfc_list:
        linear_programming(sub_model)
        rounding_to_integral(sub_model, rounding_method)

    obj_val = objective_value(model)
    accept_sfc_number = len(model.get_accepted_sfc_list())
    latency = average_latency(model)
    print("Objective Value: {} ({}, {}, {})".format(
        obj_val, evaluate(model), accept_sfc_number, latency))

    return obj_val, accept_sfc_number, latency, model.compute_resource_utilization()


def rorp(model: Model):
    return rounding_to_integral(model, rounding_one)


# Greedy
# remove configuration from topo
def is_configuration_valid(topo, sfc, configuration):
    if sfc.latency < configuration.get_latency():
        return False

    for node_pos in configuration.computing_resource:
        if configuration.computing_resource[node_pos] > topo.nodes[node_pos]['computing_resource']:
            return False

    for edge in configuration.edges:
        if sfc.throughput > topo.edges.get(edge)['bandwidth']:
            return False

    for node_pos in configuration.computing_resource:
        topo.nodes[node_pos]['computing_resource'] -= configuration.computing_resource[node_pos]

    for edge in configuration.edges:
        topo.edges.get(edge)['bandwidth'] -= sfc.throughput

    return True


def greedy(model: Model) -> (float, int, float):
    """
    Greedy thought:
        Sort sfcs by its computing resources consumption in the increasing order
        For each sfc, sort each available configuration by its latency in the increasing order
        Find the first path whose resources can fulfill the requirement of sfc
        If no available path is found, reject the sfc!
    Drawback: too slow
    """
    print("\n>>> Greedy Start <<<")

    topo = copy.deepcopy(model.topo)
    sfcs = model.sfc_list
    sfcs.sort(key=lambda x: x.computing_resources_sum)

    for idx, sfc in enumerate(sfcs):
        if DC:
            configurations = generate_configurations_dc(topo, sfc)
        else:
            configurations = generate_configurations_for_one_sfc(topo, sfc)
        configurations.sort(key=lambda x: x.get_latency())
        for configuration in configurations:
            if is_configuration_valid(topo, sfc, configuration):
                sfc.accepted_configuration = configuration
                break
        print("\r>> You have finished {}/{} sfcs' placements".format(idx +
                                                                     1, len(sfcs)), end='')

    obj_val = objective_value(model)
    accept_sfc_number = len(model.get_accepted_sfc_list())
    latency = average_latency(model)
    print("\nObjective Value: {} ({}, {}, {})".format(
        obj_val, evaluate(model), accept_sfc_number, latency))
    return obj_val, accept_sfc_number, latency


def greedy_v2(model: Model) -> (float, int, float):
    """
    Greedy thought:
        Sort sfcs by its computing resources and bandwidth consumption in the increasing order. 
        For each sfc, sort each available configuration by its latency in the increasing order. 
        Find the first path whose resources can fulfill the requirement of sfc. 
        If no available path is found, reject the sfc!
    """
    print("\n>>> Greedy Start <<<")

    topo = copy.deepcopy(model.topo)
    sfcs = model.sfc_list
    sfcs.sort(key=lambda x: x.computing_resources_sum)

    for idx, sfc in enumerate(sfcs):
        sfc.rank = idx
    sfcs.sort(key=lambda x: x.throughput)
    for idx, sfc in enumerate(sfcs):
        sfc.rank += idx
    sfcs.sort(key=lambda x: x.rank)

    for idx, sfc in enumerate(sfcs):
        configurations = generate_configurations_for_one_sfc(topo, sfc)
        configurations.sort(key=lambda x: x.get_latency())
        for configuration in configurations:
            if is_configuration_valid(topo, sfc, configuration):
                sfc.accepted_configuration = configuration
                break
        print("\r>> You have finished {}/{} sfcs' placements".format(idx +
                                                                     1, len(sfcs)), end='')

    obj_val = objective_value(model)
    accept_sfc_number = len(model.get_accepted_sfc_list())
    latency = average_latency(model)
    print("\nObjective Value: {} ({}, {}, {})".format(
        obj_val, evaluate(model), accept_sfc_number, latency))
    return obj_val, accept_sfc_number, latency


def greedy_dc(model: Model) -> (float, int, float, float):
    """
    Greedy thought:
        Sort sfcs by its computing resources consumption in the increasing
        order. For every sfc, sort each available configuration by its
        latency in the increasing order. Find the first path whose resources
        can fulfill the requirement of sfc. If no available path is found,
        reject the sfc!
    """
    print("\n>>> Greedy Start <<<")

    topo = copy.deepcopy(model.topo)
    sfcs = model.sfc_list
    sfcs.sort(key=lambda x: x.computing_resources_sum)

    for idx, sfc in enumerate(sfcs):
        configuration = generate_configuration_greedy_dc_dfs(topo, sfc)
        if configuration and is_configuration_valid(topo, sfc, configuration):
            sfc.accepted_configuration = configuration
        print("\r>> You have finished {}/{} sfcs' placements".format(idx +
                                                                     1, len(sfcs)), end='')

    obj_val = objective_value(model)
    accept_sfc_number = len(model.get_accepted_sfc_list())
    latency = average_latency(model)
    print("\nObjective Value: {} ({}, {}, {})".format(
        obj_val, evaluate(model), accept_sfc_number, latency))
    return obj_val, accept_sfc_number, latency, model.compute_resource_utilization()


def greedy_para(model: Model):
    """
        1. Sort SFCs by its computing resources in the ascending order. 
        2. For every sfc, compute its merged chain.
        3. Permute the servers to find a route and place the merged chain.
        3. Find the first path whose resources can fulfill the requirement of sfc. 
        4. If so, accept the configuraiton
        5. Otherwise, try to find the path for the origin sfc 
        6. If so, accept the configuraiton
        7. Otherwise, refuse the sfc
    """
    print("\n>>> Para Greedy Start <<<")

    topo = copy.deepcopy(model.topo)
    sfcs = model.sfc_list
    sfcs.sort(key=lambda sfc: sfc.computing_resources_sum)

    with TicToc("ParaGreedy"), PixelBar("SFC placement") as bar:
        bar.max = len(sfcs)
        for sfc in sfcs:
            # generate optimal sfc
            pa = ParaAnalyzer(sfc.vnf_list[:])
            optimal_sfc = copy.deepcopy(sfc)
            optimal_sfc.vnf_list = pa.opt_vnf_list

            optimal_config = generate_configuration_greedy_dc_dfs(
                topo, optimal_sfc)
            if optimal_config and is_configuration_valid(topo, optimal_sfc, optimal_config):
                # generate origin "place" from merge "place"
                merged_vnf_index = 0
                place = [optimal_config.place[0]]
                for para in pa.opt_strategy:
                    if para == 0:
                        merged_vnf_index += 1
                    place.append(optimal_config.place[merged_vnf_index])

                configuration = Configuration(
                    sfc, optimal_config.route, place, optimal_config.route_latency, optimal_config.idx)
                sfc.accepted_configuration = configuration
            else:
                configuration = generate_configuration_greedy_dc_dfs(topo, sfc)
                if configuration and is_configuration_valid(topo, sfc, configuration):
                    sfc.accepted_configuration = configuration
                # else reject

            bar.next()

    obj_val = objective_value(model)
    accept_sfc_number = len(model.get_accepted_sfc_list())
    latency = average_latency(model)
    print("Objective Value: {} ({}, {}, {})".format(
        obj_val, evaluate(model), accept_sfc_number, latency))
    return obj_val, accept_sfc_number, latency, model.compute_resource_utilization()

# genetic algorithm (not necessary)


def ga(model: Model):
    pass
