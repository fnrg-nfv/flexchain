import random
from typing import List
import networkx as nx

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
            # TODO: the latency of VNF could be larger, and the computing_resource is very important
            vnf_list.append(VNF(latency=random.uniform(0.2, 2), computing_resource=random.randint(400, 800)))
        s = random.randint(1, nodes_len - 1)
        d = random.randint(1, nodes_len - 1)
        while d == s:
            d = random.randint(1, nodes_len - 1)
        # TODO: the throughput requirement is very important
        ret.append(SFC(vnf_list, latency=random.randint(10, 30), throughput=random.randint(100, 1000), s=s, d=d, idx=i))
    return ret


def generate_model(topo_size: int = 100, sfc_size: int = 100) -> Model:
    topo = topology.generate_randomly(topo_size)
    sfc_list = generate_sfc_list(topo, sfc_size)
    return Model(topo, sfc_list)


# test
def main():
    model = generate_model(10, 10)
    print(model)


if __name__ == '__main__':
    main()
