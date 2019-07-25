from pulp import *

from para_placement import topology
from para_placement.config import K, EPSILON
from para_placement.model import *


def route_capacity(topo: nx.Graph, route: List):
    return sum(topo.nodes[node]['computing_resource'] for node in route)


def _generate_route_list_dc(topo: nx.Graph, sfc: SFC):
    routes = []
    queue = [([sfc.s], 0)]

    servers = [node for node in topo.nodes if topo.nodes[node]['computing_resource'] > 0]
    servers.sort(key=lambda node: topo.nodes[node]['computing_resource'], reverse=True)
    top_servers = servers[:len(sfc.vnf_list)]
    if sum(topo.nodes[server]['computing_resource'] for server in top_servers) < sfc.vnf_computing_resources_sum:
        return []

    while queue:
        route, latency = queue.pop(0)

        if latency > sfc.latency:
            continue

        if route[-1] == sfc.d and route_capacity(topo, route) >= sfc.vnf_computing_resources_sum:
            routes.append((route, latency))
            if len(routes) >= K:
                break
        else:
            adjacent_nodes = topo[route[-1]]
            for node in adjacent_nodes:

                if node in route:
                    if node in servers:
                        continue
                    loop_route = route[(len(route) - 1 - route[::-1].index(node)):]
                    overlap = [i for i in loop_route if i in servers]
                    if not overlap:
                        continue

                if sum(1 for i in route if i in servers) >= len(sfc.vnf_list) and node in servers:
                    continue

                new_route = route[:]
                new_route.append(node)
                queue.append((new_route, latency + adjacent_nodes[node]['latency']))  # latency here is not important

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
    Configuration.para = True
    topo = topology.data_center_example()
    vnf_set = generate_vnf_set(size=30)
    sfc_size = 20
    model = Model(topo, generate_sfc_list2(topo, vnf_set, sfc_size))
    model.draw_topo()

    sfc = model.sfc_list[0]
    print(sfc)
    configurations = generate_configurations_dc(topo, sfc)
    for configuration in configurations:
        print(configuration.place)


if __name__ == '__main__':
    main()
