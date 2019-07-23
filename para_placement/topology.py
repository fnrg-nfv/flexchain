import networkx as nx
import matplotlib.pyplot as plt
import random

import warnings
import matplotlib.cbook
import math

from para_placement.config import TOPO_CONFIG
from para_placement.helper import extract_str

warnings.filterwarnings("ignore", category=matplotlib.cbook.mplDeprecation)
fig, ax = plt.subplots()
fig.set_tight_layout(False)


# random generate topo with 100 nodes
# node CPU capacity: 4000~8000 Mhz
# node connectivity: log(n) / n
# edge latency: 2~5 ms
# edge bandwidth: 500~5000 Mbps todo

def generate_randomly(size: int = 100):
    topo = nx.Graph()
    for i in range(size):
        topo.add_node(i, computing_resource=random.randint(TOPO_CONFIG['CPU_LO'], TOPO_CONFIG['CPU_HI']))

    connectivity = (math.log2(size) - 2) / size
    for i in range(size):
        for j in range(i + 1, size):
            if random.uniform(0, 1) < connectivity:
                topo.add_edge(i, j, bandwidth=random.randint(TOPO_CONFIG['BW_LO'], TOPO_CONFIG['BW_HI']),
                              latency=random.uniform(TOPO_CONFIG['LT_LO'], TOPO_CONFIG['LT_HI']))

    topo.name = 'random'

    return topo


def parse_gml(gml_file='./gml_data/Geant2012.gml'):
    topo = nx.readwrite.read_gml(gml_file)

    if isinstance(topo, nx.MultiGraph):
        topo2 = nx.Graph()
        for u, v, data in topo.edges(data=True):
            w = data['LinkSpeedRaw'] if 'LinkSpeedRaw' in data else 0
            if topo2.has_edge(u, v):
                topo2[u][v]['LinkSpeedRaw'] += w
            else:
                topo2.add_edge(u, v, LinkSpeedRaw=w)
        topo = topo2

    for index, info in topo.nodes.data():
        info['computing_resource'] = random.randint(TOPO_CONFIG['CPU_LO'], TOPO_CONFIG['CPU_HI'])

    for idx, idx2, info in topo.edges.data():
        if 'LinkSpeedRaw' in info and info['LinkSpeedRaw'] > 1000000 * TOPO_CONFIG['BW_LO']:
            info["bandwidth"] = info['LinkSpeedRaw'] / 1000000
        else:
            info["bandwidth"] = random.randint(TOPO_CONFIG['BW_LO'], TOPO_CONFIG['BW_HI'])
        info['latency'] = random.uniform(TOPO_CONFIG['LT_LO'], TOPO_CONFIG['LT_HI'])

    topo.name = extract_str(gml_file)

    return topo


# test
def __main():
    topo = generate_randomly()
    print("Num of edges: ", len(topo.edges))
    print("Edges: ", topo.edges.data())
    print("Nodes: ", topo.nodes.data())

    print(topo[0])

    nx.draw(topo, with_labels=True)
    plt.show()


if __name__ == '__main__':
    __main()
