import heapq
import sys
import pickle
import random
import string
from typing import List

import matplotlib.pyplot as plt
import networkx as nx

import para_placement.config as config
from para_placement.config import SFC_CONFIG
from para_placement.helper import pairwise


class BaseObject(object):
    def __repr__(self):
        return self.__str__()


class VNF(BaseObject):
    def __init__(self, latency: float, computing_resource: int, read_fields: set = None, write_fields: set = None):
        self.latency = latency
        self.computing_resource = computing_resource
        self.read_fields = set()
        if read_fields is not None:
            self.read_fields |= read_fields
        self.write_fields = set()
        if write_fields is not None:
            self.write_fields |= write_fields

    def __str__(self):
        return "(%f, %d, %s, %s)" % (self.latency, self.computing_resource, self.read_fields, self.write_fields)

    @staticmethod
    def para_merge(vnf1, vnf2):
        merged = VNF(max(vnf1.latency, vnf2.latency),
                     vnf1.computing_resource + vnf2.computing_resource,
                     set.union(vnf1.read_fields, vnf2.read_fields),
                     set.union(vnf2.write_fields, vnf2.write_fields))
        return merged

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
    def __init__(self, vnf_list: List[VNF], latency: float, throughput: int, s, d, idx: int):
        self.vnf_list = vnf_list
        self.latency = latency
        self.throughput = throughput
        self.s = s
        self.d = d
        self.idx = idx

        self.latency_sum: float = sum(vnf.latency for vnf in vnf_list)
        self.computing_resources_sum: int = sum(
            vnf.computing_resource for vnf in vnf_list)

        self.pa = ParaAnalyzer(self.vnf_list)

        self.accepted_configuration: Configuration = None
        self.configurations: List[Configuration] = []

    def __str__(self):
        return "({}, {}, {}, {}->{}, pa:{})".format(self.vnf_list, self.latency, self.throughput, self.s, self.d, self.pa)


class Model(BaseObject):
    def __init__(self, topo: nx.Graph, sfc_list: List[SFC]):
        self.topo = topo
        self.sfc_list = sfc_list

    def __str__(self):
        return "<{}>\tState: {}\tnodes: {}\tservers: {}\tedges: {}\tSFCs: {}".format(
            self.topo.name, config.state, len(self.topo.nodes), len(self.servers()), len(self.topo.edges), len(self.sfc_list))

    def servers(self):
        return [n for n in self.topo.nodes if self.topo.nodes[n]['computing_resource'] > 0]

    def save(self, filename='model_data.pkl'):
        with open(filename, 'wb') as output:
            pickle.dump(self, output, pickle.HIGHEST_PROTOCOL)
            output.close()

    @staticmethod
    def load(filename='model_data.pkl'):
        with open(filename, 'rb') as input_file:
            model = pickle.load(input_file)
            input_file.close()
            return model

    def draw_topo(self, level=0):
        print(self)

        if level is 1:
            edges = list(self.topo.edges.data())
            print("TOPO-nodes: {}".format(self.topo.nodes.data()))
            print("TOPO-edges: ")
            edges.sort(key=lambda e: e[2]['bandwidth'])
            for info in edges:
                print(info)

        nx.draw(self.topo, with_labels=True)
        plt.show()

    def output_accepted_configuration(self, filename="ilp_result.txt"):
        with open(filename, "w+") as output:
            for sfc in self.get_accepted_sfc_list():
                output.write("C {}\t{}\n".format(
                    sfc.accepted_configuration.name, sfc.accepted_configuration))
            output.close()

    def output_configurations(self, filename="lp_result.txt"):
        with open(filename, "w+") as output:
            for sfc in self.sfc_list:
                for configuration in sfc.configurations:
                    if configuration.var.varValue > 0:
                        output.write(
                            "C {}: {}\t{}\n".format(configuration.name, configuration.var.varValue, configuration))
            output.close()

    def get_accepted_sfc_list(self):
        return list(filter(lambda s: s.accepted_configuration is not None, self.sfc_list))

    def clear(self):
        for sfc in self.sfc_list:
            sfc.accepted_configuration = None
            sfc.configurations = []

    def print_resource_usages(self, node=True, edge=True):
        accepted_sfc_list = self.get_accepted_sfc_list()

        if node:
            for node in self.topo.nodes:
                if self.topo.nodes[node]['computing_resource'] <= 0:
                    continue
                consumption = 0
                for sfc in accepted_sfc_list:
                    if node in sfc.accepted_configuration.computing_resource:
                        consumption += sfc.accepted_configuration.computing_resource[node]
                print(node, "{}/{}".format(consumption, self.topo.nodes[node]['computing_resource']),
                      "{:.2f}%".format(consumption / self.topo.nodes[node]['computing_resource'] * 100))

        if edge:
            for start, end, info in self.topo.edges.data():
                consumption = 0
                edge = (start, end)
                for sfc in accepted_sfc_list:
                    if edge in sfc.accepted_configuration.edges:
                        consumption += sfc.accepted_configuration.edges[edge] * \
                            sfc.throughput
                print(edge, "{:.2f}/{}".format(consumption, self.topo.edges.get(edge)['bandwidth']),
                      "{:.2f}%".format(consumption / self.topo.edges.get(edge)['bandwidth'] * 100))

    def compute_resource_utilization(self):
        accepted_sfc_list = self.get_accepted_sfc_list()
        usage = sum(sfc.computing_resources_sum for sfc in accepted_sfc_list)
        capacity = sum(self.topo.nodes[node]['computing_resource']
                       for node in self.topo.nodes)
        return usage / capacity


# TODO: readable fields and writeable fields should be weighted or sth else.
def generate_vnf_set(size: int = 30) -> List[VNF]:
    vnf_list = []
    readable_fields = {0, 1, 2, 3, 4}
    writeable_fields = {0, 1, 2, 3, 4}
    for i in range(size):
        latency = SFC_CONFIG.vnf_latency()
        computing_resource = SFC_CONFIG.vnf_cpu()
        read_fields = set()
        for item in readable_fields:
            if random.choice([True, False, False]):
                read_fields.add(item)
        write_fields = set()
        for item in writeable_fields:
            if random.choice([True, False, False]):
                write_fields.add(item)
        vnf_list.append(VNF(latency, computing_resource,
                            read_fields, write_fields))
    return vnf_list


# random generate 100 service function chains
# number of vnf: 3~7
# vnf computing resource: 500~1000
# vnf latency: 0.2~2 ms
# sfc latency demand: 10~30 ms
# sfc throughput demand: 32~128 Mbps todo 50~500

def generate_sfc_list_old(topo: nx.Graph, vnf_set: List[VNF], size=100, base_idx=0):
    ret = []
    for i in range(size):
        n = SFC_CONFIG.size()
        vnf_list = []
        for j in range(n):
            vnf_list.append(random.choice(vnf_set))
        nodes = list(topo.nodes.keys())
        s = random.choice(nodes)
        nodes.remove(s)
        d = random.choice(nodes)
        ret.append(SFC(vnf_list, latency=SFC_CONFIG.r_latency(),
                       throughput=SFC_CONFIG.r_throughput(), s=s, d=d, idx=i + base_idx))
    return ret


def generate_sfc_list2(topo: nx.Graph, vnf_set: List[VNF], size=100, base_idx=0):
    ret = []
    for i in range(size):
        n = SFC_CONFIG.size()
        vnf_list = []
        for j in range(n):
            vnf_list.append(random.choice(vnf_set))

        # switches = [s for s in topo.nodes if topo.nodes[s]['computing_resource'] == 0]
        top_switches = [
            s for s in topo.nodes if 'Core' in s or 'L1' in s or 'Layer 1' in s or 'Intermediate' in s]
        s = random.choice(top_switches)
        d = random.choice(top_switches)
        ret.append(SFC(vnf_list, latency=SFC_CONFIG.r_latency(),
                       throughput=SFC_CONFIG.r_throughput(), s=s, d=d, idx=i + base_idx))
    return ret


class Configuration(BaseObject):
    def __init__(self, sfc: SFC, route, place: {}, route_latency: int, idx: string):
        self.sfc = sfc
        self.route = route
        self.place = place
        self.route_latency = route_latency
        self.idx = idx
        self.name = "{}_{}".format(sfc.idx, idx)

        # computing resource
        self.computing_resource = {}
        for i, vnf in enumerate(sfc.vnf_list):
            pos = route[place[i]]
            if pos not in self.computing_resource:
                self.computing_resource[pos] = 0
            self.computing_resource[pos] += vnf.computing_resource

        # throughput
        self.edges = {}
        if config.state == config.Setting.parabox_naive:
            place_list_list = [[0]]
            if self.place:
                place_list_list.append([self.place[0]])
                for i, para in enumerate(self.sfc.pa.opt_strategy):
                    next_place = self.place[i + 1]
                    if para == 1:
                        place_list_list[-1].append(next_place)
                    else:
                        place_list_list.append([next_place])
            place_list_list.append([len(self.route)-1])

            for place_list1, place_list2 in pairwise(place_list_list):
                for sub_route in [self.route[i:j+1] for i in place_list1 for j in place_list2]:
                    for n1, n2 in pairwise(sub_route):
                        self.edges[(n1, n2)] = self.edges.setdefault(
                            (n1, n2), 0) + 1
                        self.edges[(n2, n1)] = self.edges.setdefault(
                            (n2, n1), 0) + 1
            self.place_list_list = place_list_list
        else:
            for n1, n2 in pairwise(route):
                self.edges[(n1, n2)] = self.edges.setdefault(
                    (n1, n2), 0) + 1
                self.edges[(n2, n1)] = self.edges.setdefault(
                    (n2, n1), 0) + 1

    def __str__(self):
        return "route: {}\nplace: {}\ncomputing_resource: {}\nopt_strategy: {}\nedges: {}".format(
            self.route, self.place.__str__(), self.computing_resource.__str__(), self.sfc.pa.opt_strategy, self.edges)

    # latency (normal & para)
    def get_latency(self) -> float:
        if config.state == config.Setting.normal:
            return self.route_latency + self.para_analyze()
        elif config.state == config.Setting.parabox_naive:
            return self.route_latency + self.sfc.pa.opt_latency
        elif config.state == config.Setting.nfp_naive:
            return self.route_latency + self.sfc.pa.opt_latency
        elif config.state == config.Setting.no_para:
            return self.route_latency + self.sfc.latency_sum

    # get the max resource usage ratio
    def computing_resource_ratio(self, topo: nx.Graph) -> float:
        ret = 0
        for pos in self.computing_resource:
            ret = max(
                self.computing_resource[pos] / topo.nodes.data()[pos]['computing_resource'], ret)
        return ret

    def para_analyze(self):
        """
        Get the optimal parallel execution situation using dfs
        """
        vnf_list_list = [[self.sfc.vnf_list[0]]]
        for i in range(len(self.place) - 1):
            next_vnf = self.sfc.vnf_list[i + 1]
            if self.place[i] == self.place[i + 1]:
                vnf_list_list[-1].append(next_vnf)
            else:
                vnf_list_list.append([next_vnf])

        opt_latency = 0
        for vnf_list in vnf_list_list:
            pa = ParaAnalyzer(vnf_list)
            opt_latency += pa.opt_latency

        return opt_latency


class ParaAnalyzer:
    def __init__(self, vnf_list):
        self.opt_latency = sum(vnf.latency for vnf in vnf_list)
        self.opt_vnf_list = vnf_list
        self.opt_strategy = [0 for i in range(len(vnf_list) - 1)]

        if len(vnf_list) > 0:
            self._strategy_dfs(0, vnf_list[:], [])

    def _strategy_dfs(self, index, vnf_list, strategy):
        """
        SUMMARY:
            for vnf in vnfs, find the optimal parallel strategy, and save it in "strategy".
        NOTE:
            len(strategy) == len(vnf_list) - 1
            strategy[i] indicates whether vnfs[i] and vnfs[i+1] work in parallel. 0 for no, 1 for yes
        """

        if index >= len(vnf_list) - 1:  # dfs endpoint
            latency = sum(vnf.latency for vnf in vnf_list)
            if latency < self.opt_latency:
                self.opt_latency, self.opt_strategy, self.opt_vnf_list = latency, strategy, vnf_list
        else:
            # branch 1: parallelizable
            if VNF.parallelizable_analysis(vnf_list[index], vnf_list[index + 1]) >= 0:
                new_vnf_list = vnf_list[:]
                vnf1 = new_vnf_list.pop(index)
                vnf2 = new_vnf_list.pop(index)
                merged_vnf = VNF.para_merge(vnf1, vnf2)
                new_vnf_list.insert(index, merged_vnf)

                new_strategy = strategy[:]
                new_strategy.append(1)
                self._strategy_dfs(index, new_vnf_list, new_strategy)

            # branch 2
            strategy.append(0)
            self._strategy_dfs(index + 1, vnf_list[:], strategy)

    def __str__(self):
        return "{} {}".format(self.opt_strategy, self.opt_latency)


def _dijkstra(topo: nx.Graph, s) -> {}:
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

    return ret
