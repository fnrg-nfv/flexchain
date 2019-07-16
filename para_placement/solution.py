from pulp import *

from para_placement.evaluation import evaluate, objective_value
from para_placement.model import *
import copy

epsilon = 0.03


def classic_lp(model: Model):
    print("Start Classic LP")
    problem = LpProblem("VNF Placement", LpMaximize)

    print("Variables init...")
    for sfc in model.sfc_list:
        sfc.configurations = generate_configurations_for_one_sfc(model.topo, sfc)

        # filter configurations whose latency is legal IMPORTANT
        sfc.configurations = list(filter(lambda c: c.get_latency() <= sfc.latency, sfc.configurations))

        for configuration in sfc.configurations:
            configuration.var = LpVariable(configuration.name, 0, 1, LpContinuous)

    print("Objective function init...")
    # Objective function
    problem += lpSum(
        (configuration.var * (1 - epsilon * configuration.get_latency()) for configuration in sfc.configurations)
        for
        sfc in model.sfc_list), "Total number of accept requests minus total latency"

    # Constraints
    print("Subjective function init...")
    # basic constraints
    print("Basic...")
    for sfc in model.sfc_list:
        problem += lpSum(configuration.var for configuration in sfc.configurations) <= 1.0, "Basic_{}".format(sfc.idx)

    # computing resource constraints
    print("Computing resource...")
    for index, info in model.topo.nodes.data():
        problem += lpSum(configuration.var * configuration.computing_resource[index]
                         for sfc in model.sfc_list
                         for configuration in sfc.configurations
                         if index in configuration.computing_resource) <= info['computing_resource'], "CR_{}".format(
            index)

    # throughput constraints
    print("Throughput...")
    for start, end, info in model.topo.edges.data():
        problem += lpSum(configuration.var * sfc.throughput
                         for sfc in model.sfc_list
                         for configuration in sfc.configurations
                         if "{}:{}".format(start, end) in configuration.edges) <= info[
                       'bandwidth'], "TP_{}_{}".format(start, end)

    # total number of valid sfc
    print("\nValid sfc: {}\n".format(len(list(filter(lambda s: len(s.configurations) > 0, model.sfc_list)))))

    # Problem solving
    print("Problem Solving...")
    problem.solve()
    print("Objective Value: {}".format(value(problem.objective)))

    # reduce the configurations for each sfc
    for sfc in model.sfc_list:
        sfc.configurations = list(filter(lambda c: c.var.varValue > 0, sfc.configurations))
    print("Accept sfc in LP: {}".format(len(list(filter(lambda s: len(s.configurations) > 0, model.sfc_list)))))

    # output the lp result
    with open("lp_result.txt", "w+") as output:
        for sfc in model.sfc_list:
            for configuration in sfc.configurations:
                output.write(
                    "C {}: {}\t{}\n".format(configuration.name, configuration.var.varValue, configuration))
        output.close()


# find the near optimal solution from LP
def lp_to_ilp(model: Model):
    for sfc in model.sfc_list:
        sfc.configurations.sort(key=lambda c: c.var.varValue, reverse=True)  # varValue, latency, cr ratio
    # model.sfc_list.sort(key=lambda s: s.configurations[0].get_normal_latency())  # sfc sorted by configuration latency

    # sfc sorted by computing resource ratio
    model.sfc_list.sort(key=lambda s: s.configurations[0].computing_resource_ratio(model.topo))

    # choose a configuration (maybe none) for each sfc
    for sfc in model.sfc_list:
        passed = False
        for configuration in sfc.configurations:
            sfc.accepted_configuration = configuration
            if evaluate(model):
                passed = True
                break
        if not passed:
            sfc.accepted_configuration = None

    print(evaluate(model))

    print(objective_value(model, epsilon))

    model.output_result("ilp_result.txt")


# Greedy
def is_configuration_valid(topo, sfc, configuration):
    if sfc.latency < configuration.get_latency():
        return False
    place = configuration.place
    route = configuration.route
    index = 0
    while index < len(place):
        if topo.nodes[route[place[index]]]['computing_resource'] >= sfc.vnf_list[index].computing_resource:
            topo.nodes[route[place[index]]]['computing_resource'] -= sfc.vnf_list[index].computing_resource
            index += 1
        else:
            break

    if index == len(place):
        return True
    else:
        index -= 1
        while index >= 0:
            topo.nodes[route[place[index]]]['computing_resource'] += sfc.vnf_list[index].computing_resource
        return False


def greedy(model: Model):
    """Greedy thought:
        Sort sfc's latency in increasing order
        For every sfc, sort s to d path's latency in increasing order
        Find the first path whose resources can fulfil sfc requirement
        Not find then reject!
    """

    topo = copy.deepcopy(model.topo) 
    sfcs = model.sfc_list
    sfcs.sort(key=lambda x: x.vnf_computing_resources_sum)
    # sort_sfcs_by_computing_resources(sfcs)
    for sfc in sfcs:
        configurations = generate_configurations_for_one_sfc(topo, sfc)
        configurations.sort(key=lambda x: x.get_latency())
        for configuration in configurations:
            if is_configuration_valid(topo, sfc, configuration):
                sfc.accepted_configuration = configuration
                break
            # sfc.accepted_configuration = configuration
            # if evaluate(model):
            #     break
            # if threshold > 100:
            #     break
        # if not evaluate(model):
        #     sfc.accepted_configuration = None
    if evaluate(model):
        objective_v = objective_value(model, epsilon)
        print(objective_v)
        accepted_sfc_list = list(filter(lambda s: s.accepted_configuration is not None, model.sfc_list))
        print(len(accepted_sfc_list))

    else:
        print("Greedy failed...")


def heuristic(model: Model):
    pass


def ilp(model: Model):
    pass


# genetic algorithm (not necessary)
def ga(model: Model):
    pass
