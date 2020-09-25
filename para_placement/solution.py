from progress.bar import PixelBar
from pulp import value, LpMaximize, LpContinuous, LpVariable, LpProblem, lpSum
from ttictoc import Timer

from para_placement.cg import generate_configurations, generate_configuration_greedy_dfs
from para_placement.evaluation import *
from para_placement.model import *


def linear_programming(model: Model) -> (float, int, float, float):
    print(">>> Start LP <<<")
    problem = LpProblem("VNF Placement", LpMaximize)

    with Timer(verbose_msg=f'[GenC] Elapsed time: {{}}'), PixelBar("Generating configuration sets") as bar:
        bar.max = len(model.sfc_list)
        for sfc in model.sfc_list:
            sfc.configurations = generate_configurations(model.topo, sfc)

            for configuration in sfc.configurations:
                configuration.var = LpVariable(
                    configuration.name, 0, 1, LpContinuous)

            bar.next()

    # total number of valid sfc
    config_num = sum(len(sfc.configurations) for sfc in model.sfc_list)
    valid_sfc_num = sum(len(sfc.configurations) > 0 for sfc in model.sfc_list)
    print("Number of LP Variables: {}\tValid SFC: {}".format(
        config_num, valid_sfc_num))

    with Timer(verbose_msg=f'[LP Solving] Elapsed time: {{}}'):
        # Objective function
        problem += lpSum((configuration.var for configuration in sfc.configurations)
                         for sfc in model.sfc_list), "Total number of accepted requests"

        # Constraints
        # basic constraints
        for sfc in model.sfc_list:
            problem += lpSum(
                configuration.var for configuration in sfc.configurations) <= 1.0, "Basic_{}".format(sfc.idx)

        # computing resource constraints
        for index, info in model.topo.nodes.data():
            problem += lpSum(configuration.var * configuration.computing_resource[index]
                             for sfc in model.sfc_list
                             for configuration in sfc.configurations
                             if index in configuration.computing_resource) <= info[
                           'computing_resource'], "CR_{}".format(index)

        # throughput constraints
        for start, end, info in model.topo.edges.data():
            problem += lpSum(configuration.var * sfc.throughput * configuration.edges[(start, end)]
                             for sfc in model.sfc_list
                             for configuration in sfc.configurations
                             if (start, end) in configuration.edges) <= info['bandwidth'], "TP_{}_{}".format(start, end)

        problem.solve()

    config.K = max(config.K / 3 * 2, config.K_MIN)

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
        PARC(model)


# recursively
def rounding_to_integral(model: Model, rounding_method=rounding_greedy) -> (float, int, float, float):
    print(">>> Start Rounding <<<")

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


def ROR(model: Model):
    return rounding_to_integral(model, rounding_one)


# Greedy
# validate configurationa and if valid, remove configuration from topo
def is_configuration_valid(topo, sfc, configuration, debug=False):
    if sfc.latency < configuration.get_latency():
        if debug:
            print("Latency contraint violation: {}+?={} / {}".format(
                configuration.route_latency, configuration.get_latency(), sfc.latency))
        return False

    for node_pos in configuration.computing_resource:
        if configuration.computing_resource[node_pos] > topo.nodes[node_pos]['computing_resource']:
            if debug:
                print("Computing contraint violation: {}: {} / {}".format(
                    node_pos, configuration.computing_resource[node_pos], topo.nodes[node_pos]['computing_resource']))
            return False

    for edge in configuration.edges:
        if sfc.throughput * configuration.edges[edge] > topo.edges.get(edge)['bandwidth']:
            if debug:
                print("Throughput contraint violation: {}: {} * {} / {}".format(
                    edge, configuration.edges[edge], sfc.throughput, topo.edges.get(edge)['bandwidth']))
            return False

    for node_pos in configuration.computing_resource:
        topo.nodes[node_pos]['computing_resource'] -= configuration.computing_resource[node_pos]

    for start, end, info in topo.edges.data():
        edge = (start, end)
        if edge in configuration.edges:
            topo.edges.get(edge)['bandwidth'] -= sfc.throughput * \
                                                 configuration.edges[edge]

    return True


def greedy_dc(model: Model) -> (float, int, float, float):
    """
    Greedy thought:
        Sort sfcs by its computing resources consumption in the increasing
        order. For every sfc, sort each available configuration by its
        latency in the increasing order. Find the first path whose resources
        can fulfill the requirement of sfc. If no available path is found,
        reject the sfc!
    """
    print(">>> Greedy Start <<<")

    topo = copy.deepcopy(model.topo)
    sfcs = model.sfc_list[:]
    sfcs.sort(key=lambda x: x.computing_resources_sum)

    with Timer(verbose_msg=f'[Greedy] Elapsed time: {{}}'), PixelBar("SFC placement") as bar:
        bar.max = len(sfcs)
        for sfc in sfcs:
            configuration = generate_configuration_greedy_dfs(topo, sfc)
            if configuration and is_configuration_valid(topo, sfc, configuration):
                sfc.accepted_configuration = configuration
            bar.next()

    obj_val = objective_value(model)
    accept_sfc_number = len(model.get_accepted_sfc_list())
    latency = average_latency(model)
    print("Objective Value: {} ({}, {}, {})".format(
        obj_val, evaluate(model), accept_sfc_number, latency))
    return obj_val, accept_sfc_number, latency, model.compute_resource_utilization()


def PARC(model: Model):
    """
        1. Sort SFCs by its computing resources in the ascending order.
        2. For every sfc, compute its merged chain.
        3. Find the first path whose resources can fulfill the requirement of sfc.
        4. If so, accept the configuration
        5. Otherwise, try to find the path for the origin sfc
        6. If so, accept the configuration
        7. Otherwise, refuse the sfc
    """
    print(">>> Para Greedy Start <<<")

    topo = copy.deepcopy(model.topo)
    sfcs = model.sfc_list[:]
    sfcs.sort(key=lambda sfc: sfc.computing_resources_sum)

    with Timer(verbose_msg=f'[ParaGreedy] Elapsed time: {{}}'), PixelBar("SFC placement") as bar:
        bar.max = len(sfcs)
        for sfc in sfcs:
            optimal_sfc = SFC(
                sfc.pa.opt_vnf_list[:], sfc.latency, sfc.throughput, sfc.s, sfc.d, sfc.idx)

            optimal_config = generate_configuration_greedy_dfs(
                topo, optimal_sfc)
            if optimal_config:  # generate origin "place" from the merged "place"
                merged_vnf_index = 0
                place = [optimal_config.place[0]]
                for para in sfc.pa.opt_strategy:
                    if para == 0:
                        merged_vnf_index += 1
                    place.append(optimal_config.place[merged_vnf_index])

                configuration = Configuration(
                    sfc, optimal_config.route, place, optimal_config.route_latency, optimal_config.idx)
                if is_configuration_valid(topo, sfc, configuration):
                    sfc.accepted_configuration = configuration

            if not sfc.accepted_configuration:
                configuration = generate_configuration_greedy_dfs(topo, sfc)
                if configuration and is_configuration_valid(topo, sfc, configuration):
                    sfc.accepted_configuration = configuration
            # else reject

            bar.next()

    obj_val = objective_value(model)
    accept_sfc_number = len(model.get_accepted_sfc_list())
    latency = average_latency(model)
    print("Objective Value: {} ({}, {}, {}, {})".format(
        obj_val, evaluate(model), accept_sfc_number, latency, model.compute_resource_utilization()))
    return obj_val, accept_sfc_number, latency, model.compute_resource_utilization()
