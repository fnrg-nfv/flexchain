from pulp import *

from para_placement.config import EPSILON
from para_placement.evaluation import *
from para_placement.model import *
import copy


def linear_programming(model: Model) -> (float, int, float):
    print("\n>>> Start LP <<<")
    problem = LpProblem("VNF Placement", LpMaximize)

    print(">> Variables init...")
    for idx, sfc in enumerate(model.sfc_list):
        sfc.configurations = generate_configurations_for_one_sfc(model.topo, sfc)
        print("\r>> You have generated {}/{} configuration sets".format(idx + 1, len(model.sfc_list)),
              end='')
        # filter configurations whose latency is legal. IMPORTANT
        sfc.configurations = list(filter(lambda c: c.get_latency() <= sfc.latency, sfc.configurations))

        for configuration in sfc.configurations:
            configuration.var = LpVariable(configuration.name, 0, 1, LpContinuous)

    # total number of valid sfc
    print("\nValid sfc: {}".format(sum(len(s.configurations) > 0 for s in model.sfc_list)))

    print(">> Objective function init...")
    # Objective function
    problem += lpSum(
        (configuration.var * (1 - EPSILON * configuration.get_latency()) for configuration in sfc.configurations)
        for
        sfc in model.sfc_list), "Total number of accept requests minus total latency"

    # Constraints
    print(">> Subjective function init", end="")
    # basic constraints
    print(", Basic", end="")
    for sfc in model.sfc_list:
        problem += lpSum(configuration.var for configuration in sfc.configurations) <= 1.0, "Basic_{}".format(sfc.idx)

    # computing resource constraints
    print(", Computing resource", end="")
    for index, info in model.topo.nodes.data():
        problem += lpSum(configuration.var * configuration.computing_resource[index]
                         for sfc in model.sfc_list
                         for configuration in sfc.configurations
                         if index in configuration.computing_resource) <= info['computing_resource'], "CR_{}".format(
            index)

    # throughput constraints
    print(", Throughput")
    for start, end, info in model.topo.edges.data():
        problem += lpSum(configuration.var * sfc.throughput
                         for sfc in model.sfc_list
                         for configuration in sfc.configurations
                         if (start, end) in configuration.edges) <= info[
                       'bandwidth'], "TP_{}_{}".format(start, end)

    # Problem solving
    print(">> Problem Solving...")
    problem.solve()

    # reduce the configurations for each sfc
    for sfc in model.sfc_list:
        sfc.configurations = list(filter(lambda c: c.var.varValue > 0, sfc.configurations))

    obj_val = value(problem.objective)
    accept_sfc_number = sum(len(sfc.configurations) > 0 for sfc in model.sfc_list)
    latency = 0
    if accept_sfc_number is not 0:
        latency = sum(
            configuration.get_latency() * configuration.var.varValue for sfc in model.sfc_list for configuration in
            sfc.configurations) / accept_sfc_number
    print("Objective Value: {}({}, {}ms)".format(obj_val, accept_sfc_number, latency))

    return obj_val, accept_sfc_number, latency


def rounding_one(model: Model):
    """
    Rounding method: x < 1.0 => x = 0
                     x = 1.0 => x = 1.0
    :param model:
    :return:
    """
    print(">> One Rounding <<")

    sfc_list = list(filter(lambda s: len(s.configurations) > 0, model.sfc_list))

    for sfc in sfc_list:
        for configuration in sfc.configurations:
            if configuration.var.varValue == 1:
                sfc.accepted_configuration = configuration
                if evaluate(model):
                    break
                else:
                    sfc.accepted_configuration = None

    if not model.get_accepted_sfc_list():
        rounding_greedy(model)


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
    sfc_list = list(filter(lambda s: len(s.configurations) > 0, model.sfc_list))

    for sfc in sfc_list:
        sfc.configurations.sort(key=lambda c: c.var.varValue, reverse=True)  # varValue, latency, cr ratio

    # sfc sorted by computing resource ratio
    sfc_list.sort(key=lambda s: s.configurations[0].computing_resource_ratio(model.topo))

    for sfc in sfc_list:
        for configuration in sfc.configurations:
            sfc.accepted_configuration = configuration
            if evaluate(model):
                break
            else:
                sfc.accepted_configuration = None


def rounding_to_integral(model: Model, rounding_method=rounding_greedy) -> (float, int):
    print("\n>>> Start Rounding <<<")

    rounding_method(model)

    accepted_sfc_list = model.get_accepted_sfc_list()

    if accepted_sfc_list:
        model2 = Model(copy.deepcopy(model.topo),
                       list(filter(lambda s: s.accepted_configuration is None, model.sfc_list)))
        # computing resource reduction
        for index, info in model2.topo.nodes.data():
            info['computing_resource'] -= sum(sfc.accepted_configuration.computing_resource[index]
                                              for sfc in accepted_sfc_list
                                              if index in sfc.accepted_configuration.computing_resource)
        # throughput reduction
        for start, end, info in model2.topo.edges.data():
            info['bandwidth'] -= sum(sfc.throughput
                                     for sfc in accepted_sfc_list
                                     if (start, end) in sfc.accepted_configuration.edges)
        linear_programming(model2)
        rounding_to_integral(model2, rounding_method)

    obj_val = objective_value(model, EPSILON)
    accept_sfc_number = len(model.get_accepted_sfc_list())
    latency = average_latency(model)
    print("Objective Value: {} ({}, {}, {})".format(obj_val, evaluate(model), accept_sfc_number, latency))

    return obj_val, accept_sfc_number, latency


# Greedy
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
        For every sfc, sort each available configuration by its latency in the increasing order
        Find the first path whose resources can fulfill the requirement of sfc
        If no available path is found, reject the sfc!
    """
    print("\n>>> Greedy Start <<<")

    topo = copy.deepcopy(model.topo)
    sfcs = model.sfc_list
    sfcs.sort(key=lambda x: x.vnf_computing_resources_sum)

    for idx, sfc in enumerate(sfcs):
        configurations = generate_configurations_for_one_sfc(topo, sfc)
        configurations.sort(key=lambda x: x.get_latency())
        for configuration in configurations:
            if is_configuration_valid(topo, sfc, configuration):
                sfc.accepted_configuration = configuration
                break
        print("\r>> You have finished {}/{} sfcs' placements".format(idx + 1, len(sfcs)), end='')

    obj_val = objective_value(model, EPSILON)
    accept_sfc_number = len(model.get_accepted_sfc_list())
    latency = average_latency(model)
    print("\nObjective Value: {} ({}, {}, {})".format(obj_val, evaluate(model), accept_sfc_number, latency))
    return obj_val, accept_sfc_number, latency


def greedy2(model: Model) -> (float, int, float):
    """
    Greedy thought:
        Sort sfcs by its computing resources and bandwidth consumption in the increasing order
        For every sfc, sort each available configuration by its latency in the increasing order
        Find the first path whose resources can fulfill the requirement of sfc
        If no available path is found, reject the sfc!
    """
    print("\n>>> Greedy Start <<<")

    topo = copy.deepcopy(model.topo)
    sfcs = model.sfc_list
    sfcs.sort(key=lambda x: x.vnf_computing_resources_sum)

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
        print("\r>> You have finished {}/{} sfcs' placements".format(idx + 1, len(sfcs)), end='')

    obj_val = objective_value(model, EPSILON)
    accept_sfc_number = len(model.get_accepted_sfc_list())
    latency = average_latency(model)
    print("\nObjective Value: {} ({}, {}, {})".format(obj_val, evaluate(model), accept_sfc_number, latency))
    return obj_val, accept_sfc_number, latency


# genetic algorithm (not necessary)
def ga(model: Model):
    pass
