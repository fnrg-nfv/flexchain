# DC
import sys

from pulp import *

from para_placement.config import EPSILON
from para_placement.helper import print_run_time, pairwise
from para_placement.model import *


def _bfs(topo: nx.Graph, s, d) -> ([], int):
    if (s, d) in _bfs.cache:
        return _bfs.cache[(s, d)]

    queue = [([s], 0)]

    route_list = []
    servers = [node for node in topo.nodes if topo.nodes[node]['computing_resource']]
    if d in servers:
        servers.remove(d)

    while queue:
        route, latency = queue.pop(0)

        if route[-1] == d:
            route.pop()
            route_list.append((route, latency))
        else:
            adjacent_nodes = topo[route[-1]]
            for adj_node in adjacent_nodes:
                if adj_node in route or adj_node in servers:
                    continue
                # if adjacent_nodes[adj_node]['bandwidth'] < throughput:
                #     continue
                new_route = route[:]
                new_route.append(adj_node)
                queue.append((new_route, latency + adjacent_nodes[adj_node]['latency']))

    _bfs.cache[(s, d)] = route_list
    if len(route_list) > _bfs.max:
        _bfs.max = len(route_list)
        print("Couple route MAX: {}".format(_bfs.max))

    return route_list


_bfs.cache = {}
_bfs.max = 0


# dfs + latency constraint (+ dijkstra)
def _generate_route_list_dc(topo: nx.Graph, sfc: SFC):
    routes_ret = []

    servers = [node for node in topo.nodes if topo.nodes[node]['computing_resource']]

    nodes_queue = [[]]
    cur_length = 0
    while nodes_queue:
        last_nodes = nodes_queue.pop(0)
        for node in servers:
            if node in last_nodes:
                continue
            cur_nodes = last_nodes[:]
            cur_nodes.append(node)
            routes = [([], 0)]

            # given server node, generate all routes
            for n1, n2 in pairwise([sfc.s, *cur_nodes, sfc.d]):
                sub_routes = _bfs(topo, n1, n2)
                new_routes = []
                for route, latency in routes:
                    for sub_route, sub_latency in sub_routes:
                        latency += sub_latency
                        if latency <= sfc.latency:  # pruning by latency
                            new_route = route[:]
                            new_route.extend(sub_route)
                            new_routes.append((new_route, latency))
                del routes
                routes = new_routes

            for route, latency in routes:
                route.append(sfc.d)

            routes_ret.extend(routes)

            if len(cur_nodes) > cur_length:
                cur_length = len(cur_nodes)
                print(cur_length)
            if len(cur_nodes) != len(sfc.vnf_list):
                nodes_queue.append(cur_nodes)

    return routes_ret


# bfs
def _generate_configurations_for_one_route_dc(topo: nx.Graph, route: List[int], route_latency: int, sfc: SFC,
                                              route_idx: int) -> List[Configuration]:
    sfc_length = len(sfc.vnf_list)
    server_index_list = [idx for idx, pos in enumerate(route) if topo.nodes[pos]['computing_resource']]
    server_length = len(server_index_list)

    division_set = []
    target = sfc_length - server_length
    queue = [[]]

    while queue:
        cur = queue.pop(0)
        if len(cur) == server_length - 1:
            cur.append(target - sum(cur))
            division_set.append([item + 1 for item in cur])
            continue
        cur_sum = sum(cur)
        for i in range(target - cur_sum + 1):
            cur1 = cur[:]
            cur1.append(i)
            queue.append(cur1)

    configuration_set = []
    for placement_idx, division in enumerate(division_set):
        p = []
        index = 0
        i = 0
        for _ in range(sfc_length):
            p.append(server_index_list[index])

            i += 1
            if i == division[index]:
                i = 0
                index += 1

        configuration_set.append(Configuration(sfc, route, p, route_latency, "{}_{}".format(route_idx, placement_idx)))

    return configuration_set


def _bfs_latency(topo: nx.Graph, s, d) -> float:
    if (s, d) in _bfs_latency.cache:
        return _bfs_latency.cache[(s, d)]

    queue = [([s], 0)]

    while queue:
        route, latency = queue.pop(0)

        if route[-1] == d:
            _bfs_latency.cache[(s, d)] = latency
            return latency
        else:
            adjacent_nodes = topo[route[-1]]
            for adj_node in adjacent_nodes:
                if adj_node in route:
                    continue
                new_route = route[:]
                new_route.append(adj_node)
                queue.append((new_route, latency + adjacent_nodes[adj_node]['latency']))

    return sys.maxsize


_bfs_latency.cache = {}


# all configuration for one sfc
def generate_configurations_dc(topo: nx.Graph, sfc: SFC) -> List[Configuration]:
    sfc_len = len(sfc.vnf_list)

    if sfc_len not in generate_configurations_dc.cache:
        placements = []
        servers = [node for node in topo.nodes if topo.nodes[node]['computing_resource']]
        queue = [[]]
        while queue:
            last_placement = queue.pop(0)
            for server in servers:
                cur_placement = last_placement[:]
                cur_placement.append(server)
                if len(cur_placement) == sfc_len:  # placement complete
                    placements.append(cur_placement)
                else:
                    queue.append(cur_placement)
        generate_configurations_dc.cache[sfc_len] = placements

    configuration_list = []
    for idx, placement in enumerate(generate_configurations_dc.cache[sfc_len]):
        latency = sum(_bfs_latency(topo, s, d) for s, d in pairwise([sfc.s, *placement, sfc.d]))
        configuration_list.append(DataCenterConfiguration(sfc, placement, latency, idx))

    return configuration_list


generate_configurations_dc.cache = {}


class DataCenterConfiguration(Configuration):
    def __init__(self, sfc: SFC, placement: List, route_latency: float, idx):
        self.sfc = sfc
        self.placement = placement
        self.idx = "{}_{}".format(sfc.idx, idx)
        self._route_latency = route_latency

        # computing resource
        self.computing_resource = {}
        for vnf, server in zip(sfc.vnf_list, placement):
            if server not in self.computing_resource:
                self.computing_resource[server] = 0
            self.computing_resource[server] += vnf.computing_resource

        self.l = sys.maxsize


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
    # print("\nValid sfc: {}".format(sum(len(s.configurations) > 0 for s in model.sfc_list)))

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
    # throughput constraints
    print(", Computing resource", end="")
    print(", Throughput")
    for index, info in model.topo.nodes.data():
        problem += lpSum(configuration.var * configuration.computing_resource[index]
                         for sfc in model.sfc_list
                         for configuration in sfc.configurations
                         if index in configuration.computing_resource) <= info['computing_resource'], "CR_{}".format(
            index)
        problem += lpSum(configuration.var * sfc.throughput * 2
                         for sfc in model.sfc_list
                         for configuration in sfc.configurations
                         if index in configuration.route) <= 1000, "TP_{}".format(index)

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
