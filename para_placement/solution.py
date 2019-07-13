import heapq

from pulp import *

from para_placement.model import *
from para_placement.topology import *


class Result(object):
    def __init__(self, y_r: List[int], x_rs: List[List[int]]):
        self.y_r = y_r
        self.x_rx = x_rs


class Configuration(BaseObject):
    def __init__(self, sfc: SFC, route: List[int], place: List[int], latency: int):
        # todo
        self.sfc = sfc
        self.route = route
        self.place = place
        self.latency = latency

        # computing resource
        self.computing_resource = {}
        for i in range(len(sfc.vnf_list)):
            vnf = sfc.vnf_list[i]
            pos = route[place[i]]
            self.computing_resource[pos] = vnf.computing_resource

        # throughput
        self.throughput = {}
        for i in range(len(route) - 1):
            self.throughput["%d:%d" % (route[i], route[i + 1])] = sfc.throughput
            self.throughput["%d:%d" % (route[i + 1], route[i])] = sfc.throughput

    def __str__(self):
        return self.place.__str__()


# find the shortest distance to every point
def dijkstra(topo: nx.Graph, s: int) -> {}:  # todo
    ret = {}
    heap = [(0, s)]
    while heap:
        distance, node = heapq.heappop(heap)
        if node not in ret:
            ret[node] = distance

        adj_nodes = topo[node]
        for node in adj_nodes:
            if node not in ret:
                new_distance = adj_nodes[node]['latency'] + distance
                heapq.heappush(heap, (new_distance, node))

    print("Dijkstra: {}".format(ret))
    return ret


# dfs + latency constraint (+ dijkstra)
def generate_route_list(topo: nx.Graph, sfc: SFC):
    s = sfc.s
    d = sfc.d
    shortest_distance = dijkstra(topo, d)

    stack = [([s], 0)]

    route_set = []

    while stack:
        route, latency = stack.pop()

        if latency + shortest_distance[route[-1]] > sfc.latency:
            continue

        if route[-1] == d:
            route_set.append((route, latency))
        else:
            adjacent = topo[route[-1]]
            for index in adjacent:
                if index not in route:
                    new_route = route[:]
                    new_route.append(index)
                    stack.append((new_route, latency + adjacent[index]['latency']))

    print("Size of path set: %d" % len(route_set))

    return route_set


# bfs
def generate_configuration(route: List[int], latency: int, sfc: SFC) -> List[Configuration]:
    latency += sfc.vnf_latency_sum
    if latency <= sfc.latency:
        m = len(sfc.vnf_list)
        n = len(route)

        placement_set = []
        # if n in generate_configuration.cache and m in generate_configuration.cache[n]:
        #     placement_set = generate_configuration.cache[n][m]
        # else:
        queue = [[0]]

        while queue:
            cur = queue.pop()
            if len(cur) == m + 1:
                cur.pop(0)
                placement_set.append(cur)
            else:
                for i in range(cur[-1], n):
                    add = cur[:]
                    add.append(i)
                    queue.append(add)

            # add results to the cache
            # if n not in generate_configuration.cache:
            #     generate_configuration.cache[n] = {}
            # generate_configuration.cache[n][m] = placement_set

        configuration_set = []
        for placement in placement_set:
            configuration_set.append(Configuration(sfc, route, placement, latency))
        return configuration_set


generate_configuration.cache = {}


# all configuration for one sfc
def generate_configuration_list(topo: nx.Graph, sfc: SFC) -> List[Configuration]:
    route_list = generate_route_list(topo, sfc)

    configuration_set = []
    for route, latency in route_list:
        result = generate_configuration(route, latency, sfc)
        if result:
            configuration_set.extend(result)

    print("Size of configuration set: %d" % len(configuration_set))

    return configuration_set


def classic_ilp(model: Model) -> Result:
    problem = LpProblem("VNF Placement", LpMaximize)

    total_configuration = 0
    configurations = []
    sfc_list = []
    for i in range(len(model.sfc_list)):
        configurations[i] = generate_configuration_list(model.topo, model.sfc_list[i])
        total_configuration += len(configurations[i])
        sfc = object
        sfc.var = LpVariable("sfc var %d" % i, 0, 1)
        sfc.constraints_var = LpVariable.dicts("configurations", list(range(len(configurations[i]))), 0, 1,
                                               LpContinuous)
        sfc_list[i] = sfc

    # mjt added
    for sfc in model.sfc_list:
        sfc.configurations = generate_configuration_list(model.topo, sfc)
        sfc.configurations_vars = LpVariable.dicts("configuration", list(range(len(sfc.configurations))))
        for configuration in sfc.configurations:
            configuration.x = LpVariable("", 0, 1)

    # configurations_var = LpVariable.dicts("configuration", list(range(len())))

    return Result([], [])  # todo


def greedy(model: Model) -> Result:
    pass


def heuristic(model: Model) -> Result:
    pass


def ilp(model: Model) -> Result:
    pass


# genetic algorithm (not necessary)
def ga(model: Model) -> Result:
    pass
