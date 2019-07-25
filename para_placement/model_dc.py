from pulp import *

from para_placement import topology
from para_placement.config import K, EPSILON
from para_placement.model import *


def _permutation_to_route(topo: nx.Graph, server_permutation):
    return []


def _generate_route_list_dc_by_server(topo: nx.Graph, sfc: SFC):
    routes = []
    servers = [node for node in topo.nodes if topo.nodes[node]['computing_resource'] > 0]

    for i in range(1, len(sfc.vnf_list)):
        for server_permutation in itertools.permutations(servers, i):
            server_permutation = list(server_permutation)
            if _route_capacity(topo, server_permutation) > sfc.vnf_computing_resources_sum:
                routes.append(_permutation_to_route(topo, server_permutation))
                if len(routes) > K:
                    return routes

    return routes


def _route_capacity(topo: nx.Graph, route: List):
    return sum(topo.nodes[node]['computing_resource'] for node in route)


def _generate_route_list_dc(topo: nx.Graph, sfc: SFC):
    routes = []
    queue = [([sfc.s], 0, 0)]
    sfc_len = len(sfc.vnf_list)

    servers = [node for node in topo.nodes if topo.nodes[node]['computing_resource'] > 0]
    servers.sort(key=lambda node: topo.nodes[node]['computing_resource'], reverse=True)
    top_servers = servers[:sfc_len]
    if sum(topo.nodes[server]['computing_resource'] for server in top_servers) < sfc.vnf_computing_resources_sum:
        return routes

    route_server_size_max = 0

    while queue:
        route, latency, route_servers_size = queue.pop(0)

        # route_servers_size = sum(1 for node in route if topo.nodes[node]['computing_resource'] > 0)
        if topo.nodes[route[-1]]['computing_resource'] > 0:
            route_servers_size += 1
        if route_server_size_max < route_servers_size:
            route_server_size_max = route_servers_size
            print(" -> {}".format(route_servers_size), end="")

        if route_servers_size > sfc_len:
            continue

        if latency > sfc.latency:
            continue

        if route[-1] == sfc.d and _route_capacity(topo, route) >= sfc.vnf_computing_resources_sum:
            routes.append((route, latency))
            if len(routes) >= K:
                break
        else:
            adjacent_nodes = topo[route[-1]]
            for node in adjacent_nodes:

                available = True
                for n in reversed(route):
                    if n == node:
                        available = False
                        break
                    if topo.nodes[n]['computing_resource'] > 0:
                        break
                if not available:
                    continue

                new_route = route[:]
                new_route.append(node)
                queue.append((new_route, latency + adjacent_nodes[node]['latency'],
                              route_servers_size))  # latency here is not important

    return routes


# bfs
def _generate_configurations_for_one_route_dc(topo: nx.Graph, route: List[int], route_latency: int, sfc: SFC,
                                              route_idx: int) -> List[Configuration]:
    m = len(sfc.vnf_list)
    n = len(route)

    placement_set = []
    queue = [[0]]

    while queue:
        cur = queue.pop(0)
        if len(cur) == m + 1:
            cur.pop(0)  # remove the first zero
            placement_set.append(cur)
        else:
            for i in range(cur[-1], n):
                add = cur[:]
                add.append(i)

                # check computing resource capacity
                index = len(add) - 2
                node_capacity = topo.nodes.data()[route[add[index + 1]]]['computing_resource']
                usage = sfc.vnf_list[index].computing_resource
                while index > 0 and add[index + 1] == add[index]:
                    index -= 1
                    usage += sfc.vnf_list[index].computing_resource
                if usage <= node_capacity:
                    queue.append(add)

    configuration_set = []
    for idx, placement in enumerate(placement_set):
        configuration_set.append(Configuration(sfc, route, placement, route_latency, "{}_{}".format(route_idx, idx)))
    return configuration_set


def generate_configurations_dc(topo: nx.Graph, sfc: SFC) -> List[Configuration]:
    configurations = []
    routes = _generate_route_list_dc(topo, sfc)

    print(" ... Size of route_list: {}".format(len(routes)), end="")

    for idx, item in enumerate(routes):
        route, route_latency = item
        configurations.extend(_generate_configurations_for_one_route_dc(topo, route, route_latency, sfc, idx))

    return configurations


def linear_programming_dc(model: Model) -> (float, int, float):
    print("\n>>> Start LP <<<")
    problem = LpProblem("VNF Placement", LpMaximize)

    print(">> Variables init...")
    for idx, sfc in enumerate(model.sfc_list):
        sfc.configurations = generate_configurations_dc(model.topo, sfc)
        print("\r>> You have generated {}/{} configuration sets".format(idx + 1, len(model.sfc_list)), end='')
        # filter configurations whose latency is legal. IMPORTANT
        sfc.configurations = list(filter(lambda c: c.get_latency() <= sfc.latency, sfc.configurations))

        for configuration in sfc.configurations:
            configuration.var = LpVariable(configuration.name, 0, 1, LpContinuous)

    # total number of valid sfc
    print()
    print("Number of LP Variables: {}".format(sum(len(sfc.configurations) for sfc in model.sfc_list)))
    print("Valid sfc: {}".format(sum(len(s.configurations) > 0 for s in model.sfc_list)))

    print(">> Objective function init...")
    # Objective function
    problem += lpSum(
        (configuration.var * (1 - EPSILON * configuration.get_latency()) for configuration in sfc.configurations)
        for sfc in model.sfc_list), "Total number of accept requests minus total latency"

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
        problem += lpSum(configuration.var * sfc.throughput * configuration.edges[(start, end)]
                         for sfc in model.sfc_list
                         for configuration in sfc.configurations
                         if (start, end) in configuration.edges) <= info['bandwidth'], "TP_{}_{}".format(start, end)

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


def main():
    list1 = range(1, 17)
    ret = []
    # for i in range(1, 4):
    #     ret.append(list())
    idx = 0
    for i in itertools.permutations(list1, 1):
        print(list(i))
        idx += 1
        if idx > 100:
            break


if __name__ == '__main__':
    main()
