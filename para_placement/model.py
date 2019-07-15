import heapq
import pickle
import random
import string
from typing import List
import networkx as nx
import matplotlib.pyplot as plt

from para_placement import topology


class BaseObject(object):
    def __repr__(self):
        return self.__str__()


class VNF(BaseObject):
    def __init__(self, latency: float, computing_resource: int, read_fields: set = None, write_fields: set = None):
        self.latency = latency
        self.computing_resource = computing_resource
        self.read_fields = read_fields
        self.write_fields = write_fields

    def __str__(self):
        return "(%f, %d)" % (self.latency, self.computing_resource)

    @staticmethod
    def parallelizable_analysis(vnf1, vnf2):
        """Analysis whether two vnf can execute parallelism.
        
        Returns:
        0 for packet copy
        1 for no need packet copy
        -1 for cannot parallelism
        """
        nf1_read_fields = vnf1.read_fields
        nf1_write_fields = vnf1.write_fields
        nf2_read_fields = vnf2.read_fields
        nf2_write_fields = vnf2.write_fields

        # analyse read after write
        for fields1 in nf1_write_fields:
            for fields2 in nf2_read_fields:
                if fields1 == fields2:
                    return -1  # cannot parallelism

        # analyse write after read
        for fields1 in nf1_read_fields:
            for fields2 in nf2_write_fields:
                if fields1 == fields2:
                    return 0  # need packet copy

        # analyse write after write
        for fields1 in nf1_write_fields:
            for fields2 in nf2_write_fields:
                if fields1 == fields2:
                    return 0  # need packet copy

        return 1  # perfect parallelism


class SFC(BaseObject):
    def __init__(self, vnf_list: List[VNF], latency: float, throughput: int, s: int, d: int, idx: int):
        self.vnf_list = vnf_list
        self.latency = latency
        self.throughput = throughput
        self.s = s
        self.d = d
        self.idx = idx

        self.vnf_latency_sum: float = 0
        self.accepted_configuration: Configuration = None
        for vnf in vnf_list:
            self.vnf_latency_sum += vnf.latency

    def __str__(self):
        return "({}, {}, {}, {}->{})".format(self.vnf_list, self.latency, self.throughput, self.s, self.d)


class Model(BaseObject):
    def __init__(self, topo: nx.Graph, sfc_list: List[SFC]):
        self.topo = topo
        self.sfc_list = sfc_list

    def __str__(self):
        return "TOPO-nodes:{}\nTOPO-edges:{}\nSFCs:{}".format(self.topo.nodes.data(), self.topo.edges.data(),
                                                              self.sfc_list)

    def save(self, file_name='model_data.pkl'):
        with open(file_name, 'wb') as output:
            pickle.dump(self, output, pickle.HIGHEST_PROTOCOL)
            output.close()

    @staticmethod
    def load(file_name='model_data.pkl'):
        with open(file_name, 'rb') as input_file:
            model = pickle.load(input_file)
            input_file.close()
            return model

    def draw_topo(self):
        nx.draw(self.topo, with_labels=True)
        plt.show()

    def output_result(self, filename="result.txt"):
        with open(filename, "w+") as output:
            for sfc in filter(lambda s: s.accepted_configuration is not None, self.sfc_list):
                output.write(
                    "C {}: {}\t{}\n".format(sfc.accepted_configuration.name, sfc.accepted_configuration.var.varValue,
                                            sfc.accepted_configuration))
            output.close()


# random generate 100 service function chains
# number of vnf: 5~10
# vnf computing resource: 500~1000
# vnf latency: 0.2~2 ms
# sfc latency demand: 10~30 ms
# sfc throughput demand: 32~128 Mbps todo

def generate_sfc_list(topo: nx.Graph, size=100):
    ret = []
    nodes_len = len(topo.nodes)
    for i in range(size):
        n = random.randint(5, 10)
        vnf_list = []
        for j in range(n):
            vnf_list.append(VNF(latency=random.uniform(0.2, 2), computing_resource=random.randint(400, 800)))
        s = random.randint(1, nodes_len - 1)
        d = random.randint(1, nodes_len - 1)
        while d == s:
            d = random.randint(1, nodes_len - 1)
        ret.append(SFC(vnf_list, latency=random.randint(10, 30), throughput=random.randint(100, 1000), s=s, d=d, idx=i))
    return ret


def generate_model(topo_size: int = 100, sfc_size: int = 100) -> Model:
    topo = topology.generate_randomly(topo_size)
    sfc_list = generate_sfc_list(topo, sfc_size)
    return Model(topo, sfc_list)


class Configuration(BaseObject):
    def __init__(self, sfc: SFC, route: List[int], place: List[int], route_latency: int, idx: string):
        self.sfc = sfc
        self.route = route
        self.place = place
        self._route_latency = route_latency
        # self.latency = route_latency + sfc.vnf_latency_sum
        self.name = "{}_{}".format(sfc.idx, idx)

        # computing resource
        self.computing_resource = {}
        for i, vnf in enumerate(sfc.vnf_list):
            pos = route[place[i]]
            if pos not in self.computing_resource:
                self.computing_resource[pos] = 0
            self.computing_resource[pos] += vnf.computing_resource

        # throughput
        self.edges = []
        for i in range(len(route) - 1):
            start = max(route[i], route[i + 1])
            end = min(route[i], route[i + 1])
            self.edges.append("%d:%d" % (start, end))

        self.l = 9999999  # used to find optimal situation

    def __str__(self):
        return "route: {}\tplace: {}\tcomputing_resource: {}".format(self.route.__str__(), self.place.__str__(),
                                                                     self.computing_resource.__str__())

    para = False

    # latency (normal & para)
    def get_latency(self) -> float:
        if Configuration.para:
            return 1  # todo

        return self._route_latency + self.sfc.vnf_latency_sum

    # get the max resource usage ratio
    def computing_resource_ratio(self, topo: nx.Graph) -> float:
        ret = 0
        for pos in self.computing_resource:
            ret = max(self.computing_resource[pos] / topo.nodes.data()[pos]['computing_resource'], ret)
        return ret

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
        return optimal_para

    def backtracking_analysis(self, index, vnfs, analysis_result, result):
        """
        for vnf in vnfs, find the optimal parallelism situation and save result in result.
        len(result) = len(vnfs) - 1
        result[i] indicates vnfs[i] and vnfs[i+1] whether execute parallelism. 0 for no, 1 for yes
        """
        if index == len(vnfs) - 1:
            # analysis end, compute latency
            l = 0
            for vnf in vnfs:
                l = l + vnf.latency
            if l < self.l:
                # find a better situation
                self.l = l
                result.clear()
                result.extend(analysis_result)
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


def _dijkstra(topo: nx.Graph, s: int) -> {}:  # todo
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
def _generate_route_list(topo: nx.Graph, sfc: SFC):
    s = sfc.s
    d = sfc.d

    shortest_distance = _dijkstra(topo, d)
    if s not in shortest_distance:
        return []

    stack = [([s], 0)]

    route_set = []

    while stack:
        route, latency = stack.pop()

        if latency + shortest_distance[route[-1]] > sfc.latency:  # partial latency constraints
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
def _generate_configurations_for_one_route(topo: nx.Graph, route: List[int], route_latency: int, sfc: SFC, idx: int) \
        -> List[Configuration]:
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
    for idx2, placement in enumerate(placement_set):
        configuration_set.append(Configuration(sfc, route, placement, route_latency, "{}_{}".format(idx, idx2)))
    return configuration_set


# all configuration for one sfc
def generate_configurations_for_one_sfc(topo: nx.Graph, sfc: SFC) -> List[Configuration]:
    route_list = _generate_route_list(topo, sfc)

    configuration_list = []
    for idx, item in enumerate(route_list):
        route, latency = item
        configuration_list.extend(_generate_configurations_for_one_route(topo, route, latency, sfc, idx))

    print("Size of configuration set: %d" % len(configuration_list))

    return configuration_list


# test
def main():
    model = generate_model(10, 10)
    print(model)


if __name__ == '__main__':
    main()
