from pulp import *

from para_placement.evaluation import evaluate, objective_value
from para_placement.model import *

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

    print("Problem Solving...")
    # LpSolverDefault.msg = 1
    problem.solve()
    print("Objective Value: {}".format(value(problem.objective)))

    # reduce the configurations for each sfc
    for sfc in model.sfc_list:
        sfc.configurations = list(filter(lambda c: c.var.varValue > 0, sfc.configurations))
    model.sfc_list = list(filter(lambda s: len(s.configurations) > 0, model.sfc_list))  # reduce configurations
    print("Accept sfc in LP: {}".format(len(model.sfc_list)))

    # output the lp result
    model.output_result("lp_result.txt")


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

    # rounding
    # count = 0
    # while count < 200:
    #     count += 1
    #     print("Rounding...{}".format(count))
    #
    #     for sfc in model.sfc_list:
    #         x_sum = sum(configuration.var.varValue for configuration in sfc.configurations)
    #         if random.uniform(0, 1) <= x_sum:  # accepted
    #             choose_random = random.uniform(0, 1)
    #             for configuration in sfc.configurations:
    #                 if configuration.var.varValue > 0:
    #                     partial = configuration.var.varValue / x_sum
    #                     if choose_random <= partial:
    #                         sfc.accepted_configuration = configuration
    #                         break
    #                     else:
    #                         choose_random -= partial
    #         else:  # rejected
    #             sfc.accepted_configuration = None
    #
    #     if evaluate(model):
    #         print("Accepted")
    #         break
    #     print("Rejected")

    print(objective_value(model, epsilon))

    model.output_result("ilp_result.txt")


# Greedy
def sort_sfcs_by_computing_resources(sfcs):
    for i in range(1, len(sfcs)):
        for j in range(i, 0, -1):
            if sfcs[j].vnf_computing_resources_sum < sfcs[j - 1].vnf_computing_resources_sum:
                sfcs[j], sfcs[j - 1] = sfcs[j - 1], sfcs[j]
            else:
                break


def sort_route_list_by_capacity_divide_latency(topo, route_list):
    """
    Sort all possible path by path_capacity/path_latency in decreasing order
    """
    ranked_path = []
    for path in route_list:
        path_latency = path[1]
        path_capacity = 0
        for node_index in path[0]:
            path_capacity += topo.nodes[node_index]['computing_resource']
        ranked_path.append(list(path).append(path_capacity / path_latency))
    for i in range(1, len(ranked_path)):
        for j in range(i, 0, -1):
            if ranked_path[j][2] > ranked_path[j - 1][2]:
                ranked_path[j], ranked_path[j - 1] = ranked_path[j - 1], ranked_path[j]
            else:
                break
    return ranked_path


def place_sfc_with_parallelism_concern(topo, sfc, ranked_path):
    pass


def greedy(model: Model):
    """Greedy thought: 
        Sort sfc's latency in increasing order
        For every sfc, sort s to d path's latency in increasing order
        Find the first path whose resources can fulfil sfc requirement
        Not find then reject!
    """

    # print("Start greedy")
    # num_of_accept_sfcs = 0
    # greedy_result = []
    # print("Sort sfcs...")
    # sfcs = model.sfc_list
    # sort_sfcs_by_latency(sfcs)
    # print("Sort sfcs successfully...")

    # print("Handle sfc one by one...")
    # topo = model.topo
    # for sfc in sfcs:
    #     sfc_reject = 1
    #     vnf_process_latency = 0
    #     for vnf in sfc.vnf_list:
    #         vnf_process_latency += vnf.latency
    #     route_list = generate_route_list(topo, sfc)
    #     ranked_path = sort_route_list_by_capacity_divide_latency(topo, route_list)

    #     for route in ranked_path:
    #         path, path_latency = route
    #         place = []
    #         total_latency = vnf_process_latency + path_latency
    #         if total_latency < sfc.latency:
    #             path_index = 0
    #             vnf_index = 0
    #             while path_index < len(path) and vnf_index < len(sfc.vnf_list):
    #                 if topo.nodes[path[path_index]]['computing_resource'] >= sfc.vnf_list[vnf_index].computing_resource:
    #                     place.append(path_index)
    #                     topo.nodes[path[path_index]]['computing_resource'] -= sfc.vnf_list[vnf_index].computing_resource
    #                     vnf_index += 1
    #                 else:
    #                     path_index += 1

    #             if vnf_index >= len(sfc.vnf_list):
    #                 # we successfully put this sfc in this route
    #                 sfc_reject = 0
    #                 num_of_accept_sfcs += 1
    #                 greedy_result.append((sfc, 1, path, place))
    #             else:
    #                 # This route cannot work. add deleted computing resources back
    #                 vnf_index -= 1
    #                 while vnf_index >= 0:
    #                     topo.node[path[place.pop()]]['computing_resource'] += sfc.vnf_list[vnf_index].computing_resource
    #                     vnf_index -= 1
    #         else:
    #             break
    #         if sfc_reject == 0:
    #             break
    #     if sfc_reject == 1:
    #         greedy_result.append((sfc, 0, [], []))


    topo = model.topo
    sfcs = model.sfc_list
    sort_sfcs_by_computing_resources(sfcs)


    print("Handle finished...")
    print("Result:", greedy_result)  # TODO: show result detail


def heuristic(model: Model):
    pass


def ilp(model: Model):
    pass


# genetic algorithm (not necessary)
def ga(model: Model):
    pass
