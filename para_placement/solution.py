import heapq

from pulp import *

from para_placement.model import *


class Result(object):
    def __init__(self, y_r: List[int], x_rs: List[List[int]]):
        self.y_r = y_r
        self.x_rx = x_rs


class Configuration(BaseObject):
    def __init__(self, sfc: SFC, route: List[int], place: List[int], latency: int, idx: string):
        self.sfc = sfc
        self.route = route
        self.place = place
        self.latency = latency
        self.name = "{}_{}".format(sfc.idx, idx)
        self.l = 9999999  #used to find optimal situation

        # computing resource
        self.computing_resource = {}
        for i in range(len(sfc.vnf_list)):
            vnf = sfc.vnf_list[i]
            pos = route[place[i]]
            if pos not in self.computing_resource:
                self.computing_resource[pos] = 0
            self.computing_resource[pos] += vnf.computing_resource

        # throughput
        self.throughput = []
        for i in range(len(route) - 1):
            start = max(route[i], route[i + 1])
            end = min(route[i], route[i + 1])
            self.throughput.append("%d:%d" % (start, end))

    def __str__(self):
        return self.place.__str__()

    def para_latency_analysis(self):
        """Get the optimal paralle execution situation using backtracking
        """
        optimal_para = []
        vnfs = [self.sfc.vnf_list[0]]
        for i in range(len(self.place)-1):
            if(self.place[i] == self.place[i+1]):
                vnfs.append(self.sfc.vnf_list[i+1])
            else:
                if(len(vnfs)>1):
                    result = []
                    self.l = 999999
                    self.backtracking_analysis(0, vnfs, [], result)
                    optimal_para.extend(result)
                    optimal_para.append(0)
                    vnfs = [self.sfc.vnf_list[i+1]]
                else:
                    optimal_para.append(0)
                    vnfs = [self.sfc.vnf_list[i+1]]
        if(len(vnfs)>1):
            result = []
            self.l = 999999
            self.backtracking_analysis(0, vnfs, [], result)
            optimal_para.extend(result)
        return optimal_para

    def backtracking_analysis(self, index, vnfs, analysis_result, result):
        '''for vnf in vnfs, find the optimal parallelism situation and save resule in result.
        len(result) = len(vnfs) - 1
        result[i] indicates vnfs[i] and vnfs[i+1] whether execute parallelism. 0 for no, 1 for yes
        '''
        if (index == len(vnfs) - 1):
            #analysis end, compute latency
            l = 0
            for vnf in vnfs:
                l = l + vnf.latency
            if (l < self.l):
                #find a better situation
                self.l = l
                result = analysis_result
            return
        if (VNF.parallelizable_analysis(vnfs[index], vnfs[index + 1]) >= 0):
            #parallelizable
            vnf1 = vnfs.pop(index)
            vnf2 = vnfs.pop(index)
            new_vnf = VNF(max(vnf1.latency, vnf2.latency),
                          vnf1.computing_resource + vnf2.computing_resource,
                          set.union(vnf1.read_fields, vnf2.read_fields),
                          set.union(vnf1.write_fields, vnf2.write_fields))
            vnfs.insert(index, new_vnf)
            analysis_result.append(1)
            self.backtracking_analysis(index, vnfs, analysis_result, result)
            vnfs.pop(index)
            vnfs.insert(index, vnf2)
            vnfs.insert(index, vnf1)
            analysis_result.pop()
            analysis_result.append(0)
            self.backtracking_analysis(index + 1, vnfs, analysis_result,
                                       result)
            analysis_result.pop() 
        else:
            analysis_result.append(0)
            self.backtracking_analysis(index + 1, vnfs, analysis_result,
                                       result)
            analysis_result.pop() 


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
    if s not in shortest_distance:
        return []

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
                    stack.append(
                        (new_route, latency + adjacent[index]['latency']))

    print("Size of path set: %d" % len(route_set))

    return route_set


# bfs
def generate_configuration(route: List[int], latency: int, sfc: SFC, idx: int) -> List[Configuration]:
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
        for idx2, placement in enumerate(placement_set):
            configuration_set.append(Configuration(sfc, route, placement, latency, "{}_{}".format(idx,idx2)))
        return configuration_set


generate_configuration.cache = {}


# all configuration for one sfc
def generate_configuration_list(topo: nx.Graph,
                                sfc: SFC) -> List[Configuration]:
    route_list = generate_route_list(topo, sfc)

    configuration_list = []
    for idx, item in enumerate(route_list):
        route, latency = item
        result = generate_configuration(route, latency, sfc, idx)
        if result:
            configuration_list.extend(result)

    print("Size of configuration set: %d" % len(configuration_list))

    return configuration_list


epsilon = 0


def classic_ilp(model: Model) -> Result:
    print("Start Classic LP")
    problem = LpProblem("VNF Placement", LpMaximize)

    print("Variables init...")
    for sfc in model.sfc_list:
        sfc.configurations = generate_configuration_list(model.topo, sfc)
        for configuration in sfc.configurations:
            configuration.var = LpVariable(configuration.name, 0, 1, LpContinuous)

    print("Objective function init...")
    # Objective function
    problem += lpSum(
        (configuration.var * (1 - epsilon * configuration.latency) for configuration in sfc.configurations) for
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
                         if "{}:{}".format(start, end) in configuration.throughput) <= info[
                       'bandwidth'], "TP_{}_{}".format(start, end)
    valid_sfc = 0
    for sfc in model.sfc_list:
        if len(sfc.configurations) > 0:
            valid_sfc += 1
    print("\nValid sfc: {}\n".format(valid_sfc))

    print("Problem Objective:")
    print(problem.objective)
    LpSolverDefault.msg = 1
    print("Problem Solving...")
    problem.solve()

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
