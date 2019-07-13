import heapq

from pulp import *

from para_placement.model import *


class Result(object):
    def __init__(self, y_r: List[int], x_rs: List[List[int]]):
        self.y_r = y_r
        self.x_rx = x_rs


class Configuration(object):
    def __init__(self, sfc: SFC, route: List[int], place: List[int], latency: int):
        # todo
        self.sfc = sfc
        self.route = route
        self.place = place
        self.latency = latency
        # self.throughput = throughput
        # self.computing_resource = computing_resource


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
        elif route[-1] == d:
            route_set.append((route, latency))
        else:
            adjs = topo[route[-1]]
            for adj in adjs:
                if adj not in route:
                    new_route = route[:]
                    new_route.append(adj)
                    stack.append((new_route, latency + adjs[adj]['latency']))

    print("Size of path set: %d" % len(route_set))

    return route_set


def generate_configuration(topo: nx.Graph, sfc: SFC) -> List[Configuration]:
    route_list = generate_route_list(topo, sfc)
    vnf_latency = 0
    for vnf in sfc.vnf_list:
        vnf_latency += vnf.latency

    configuration_set = []
    n = len(sfc.vnf_list)
    for route, latency in route_list:
        latency += vnf_latency
        if latency > sfc.latency:
            continue
        queue = [[0]]
        m = len(route)

        while queue:
            cur = queue.pop()
            if len(cur) == n + 1:
                cur.pop(0)
                configuration_set.append(Configuration(sfc, route, cur, latency))
                pass
            else:
                for i in range(cur[-1], m):
                    add = cur[:]
                    add.append(i)
                    queue.append(add)

    print("Size of configuration set: %d" % len(configuration_set))

    return configuration_set


def classic_ilp(model: Model) -> Result:
    problem = LpProblem("VNF Placement", LpMaximize)
    return Result([], [])


def greedy(model: Model) -> Result:
    pass


def heuristic(model: Model) -> Result:
    pass


def ilp(model: Model) -> Result:
    pass


# genetic algorithm (not necessary)
def ga(model: Model) -> Result:
    pass
