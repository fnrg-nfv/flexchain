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
        self.l = 9999999  # used to find optimal situation

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

    def para_latency_analysis(self) -> float:
        """
        Get the optimal parallel execution situation using backtracking
        """
        optimal_para = []
        vnfs = [self.sfc.vnf_list[0]]
        for i in range(len(self.place) - 1):
            if self.place[i] == self.place[i + 1]:
                vnfs.append(self.sfc.vnf_list[i + 1])
            else:
                if len(vnfs) > 1:
                    result = []
                    self.l = 999999
                    self.backtracking_analysis(0, vnfs, [], result)
                    optimal_para.extend(result)
                    optimal_para.append(0)
                    vnfs = [self.sfc.vnf_list[i + 1]]
                else:
                    optimal_para.append(0)
                    vnfs = [self.sfc.vnf_list[i + 1]]
        if len(vnfs) > 1:
            result = []
            self.l = 999999
            self.backtracking_analysis(0, vnfs, [], result)
            optimal_para.extend(result)
        
        total_latency = 0
        sub_chain_latency = self.sfc.vnf_list[0].latency
        for i in range(len(optimal_para)):
            if optimal_para[i] == 1:
                sub_chain_latency = max(sub_chain_latency, self.sfc.vnf_list[i+1])
            else:
                total_latency += sub_chain_latency
                sub_chain_latency = self.sfc.vnf_list[i+1]
        total_latency += sub_chain_latency

        return total_latency

    def backtracking_analysis(self, index, vnfs, analysis_result, result):
        """
        for vnf in vnfs, find the optimal parallelism situation and save resule in result.
        len(result) = len(vnfs) - 1
        result[i] indicates vnfs[i] and vnfs[i+1] whether execute parallelism. 0 for no, 1 for yes

        :param index:
        :param vnfs:
        :param analysis_result:
        :param result:
        :return:
        """
        if index == len(vnfs) - 1:
            # analysis end, compute latency
            l = 0
            for vnf in vnfs:
                l = l + vnf.latency
            if l < self.l:
                # find a better situation
                self.l = l
                result = analysis_result
            return
        if VNF.parallelizable_analysis(vnfs[index], vnfs[index + 1]) >= 0:
            # parallelizable
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
            configuration_set.append(Configuration(sfc, route, placement, latency, "{}_{}".format(idx, idx2)))
        return configuration_set


generate_configuration.cache = {}


# all configuration for one sfc
def generate_configuration_list(topo: nx.Graph, sfc: SFC) -> List[Configuration]:
    route_list = generate_route_list(topo, sfc)

    configuration_list = []
    for idx, item in enumerate(route_list):
        route, latency = item
        result = generate_configuration(route, latency, sfc, idx)
        if result:
            configuration_list.extend(result)

    print("Size of configuration set: %d" % len(configuration_list))

    return configuration_list


epsilon = 0.01


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

    # print("Problem Objective:\n", problem.objective)
    LpSolverDefault.msg = 1
    print("\nProblem Solving...")
    problem.solve()

    return Result([], [])  # todo


def sort_sfcs_by_latency(sfcs):
    for i in range(1, len(sfcs)):
        for j in range(i, 0, -1):
            if sfcs[j].latency < sfcs[j-1].latency:
                sfcs[j], sfcs[j-1] = sfcs[j-1], sfcs[j]
            else:
                break

def sort_route_list_by_capacity_divide_latency(topo, route_list):
    '''Sort all possible path by path_capacity/path_latency in decreasing order
    '''
    ranked_path = []
    for path in route_list:
        path_latency = path[1]
        path_capacity = 0
        for node_index in path[0]:
            path_capacity += topo.nodes[node_index]['computing_resource']
        ranked_path.append(list(path).append(path_capacity/path_latency))
    for i in range(1, len(ranked_path)):
        for j in range(i, 0, -1):
            if ranked_path[j][2] > ranked_path[j-1][2]:
                ranked_path[j], ranked_path[j-1] = ranked_path[j-1], ranked_path[j]
            else:
                break
    return ranked_path

def place_sfc_with_parallelism_concern(topo, sfc, ranked_path) -> (sfc, accept_or_not, path, place):
    pass
    
def greedy(model: Model) -> Result:
    '''Greedy thought: 
        Sort sfc's latency in increasing order
        For every sfc, sort s to d path's latency in increasing order
        Find the first path whose resources can fulfil sfc requirement
        Not find then reject! 
    '''
    print("Start greedy")
    num_of_accept_sfcs = 0
    greedy_result = []
    print("Sort sfcs...")
    sfcs = model.sfc_list
    sort_sfcs_by_latency(sfcs)
    print("Sort sfcs successfully...")

    print("Handle sfc one by one...")
    topo = model.topo
    for sfc in sfcs:
        sfc_reject = 1
        vnf_process_latency = 0
        for vnf in sfc.vnf_list:
            vnf_process_latency += vnf.latency
        route_list = generate_route_list(topo, sfc)
        ranked_path = sort_route_list_by_capacity_divide_latency(topo, route_list)
        
        for route in ranked_path:
            path, path_latency = route
            place = []
            total_latency = vnf_process_latency + path_latency
            if total_latency<sfc.latency:
                path_index = 0
                vnf_index = 0
                while path_index < len(path) and vnf_index < len(sfc.vnf_list):
                    if topo.nodes[path[path_index]]['computing_resource'] >= sfc.vnf_list[vnf_index].computing_resource:
                        place.append(path_index)
                        topo.nodes[path[path_index]]['computing_resource'] -= sfc.vnf_list[vnf_index].computing_resource
                        vnf_index +=1
                    else:
                        path_index +=1

                if vnf_index >= len(sfc.vnf_list):
                    #we successfully put this sfc in this route
                    sfc_reject = 0
                    num_of_accept_sfcs += 1 
                    greedy_result.append((sfc, 1, path, place))
                else:
                    #This route cannot work. add deleted computing resources back
                    vnf_index -=1
                    while vnf_index>=0:
                        topo.node[path[place.pop()]]['computing_resource'] += sfc.vnf_list[vnf_index].computing_resource
                        vnf_index -=1
            else:
                break
            if sfc_reject == 0:
                break
        if sfc_reject == 1:
            greedy_result.append((sfc, 0, [], []))

    print("Handle finished...")
    print("Result:", greedy_result) #TODO: show result detail




def heuristic(model: Model) -> Result:
    pass


def ilp(model: Model) -> Result:
    pass


# genetic algorithm (not necessary)
def ga(model: Model) -> Result:
    pass
