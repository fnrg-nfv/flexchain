import random
import warnings

import math
import matplotlib.cbook
import matplotlib.pyplot as plt
import networkx as nx

from para_placement.config import TOPO_CONFIG, TOPO_CONFIG2
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
        topo.add_node(i, computing_resource=TOPO_CONFIG2.cpu())

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
            info["bandwidth"] = 1000
        info['latency'] = random.uniform(TOPO_CONFIG['LT_LO'], TOPO_CONFIG['LT_HI'])

    topo.name = extract_str(gml_file)

    return topo


def data_center_example():
    topo = nx.Graph()
    topo.add_node("L1 S 1", computing_resource=0)
    topo.add_node("L1 S 2", computing_resource=0)
    topo.add_node("L2 S 1 1", computing_resource=0)
    topo.add_node("L2 S 1 2", computing_resource=0)
    topo.add_node("L2 S 1 3", computing_resource=0)
    topo.add_node("L2 S 1 4", computing_resource=0)
    topo.add_node("L2 S 2 1", computing_resource=0)
    topo.add_node("L2 S 2 2", computing_resource=0)
    topo.add_node("L2 S 2 3", computing_resource=0)
    topo.add_node("L2 S 2 4", computing_resource=0)
    topo.add_node("N 1 1", computing_resource=TOPO_CONFIG2.cpu())
    topo.add_node("N 1 2", computing_resource=TOPO_CONFIG2.cpu())
    topo.add_node("N 1 3", computing_resource=TOPO_CONFIG2.cpu())
    topo.add_node("N 1 4", computing_resource=TOPO_CONFIG2.cpu())
    topo.add_node("N 1 5", computing_resource=TOPO_CONFIG2.cpu())
    topo.add_node("N 1 6", computing_resource=TOPO_CONFIG2.cpu())
    topo.add_node("N 1 7", computing_resource=TOPO_CONFIG2.cpu())
    topo.add_node("N 1 8", computing_resource=TOPO_CONFIG2.cpu())
    topo.add_node("N 2 1", computing_resource=TOPO_CONFIG2.cpu())
    topo.add_node("N 2 2", computing_resource=TOPO_CONFIG2.cpu())
    topo.add_node("N 2 3", computing_resource=TOPO_CONFIG2.cpu())
    topo.add_node("N 2 4", computing_resource=TOPO_CONFIG2.cpu())
    topo.add_node("N 2 5", computing_resource=TOPO_CONFIG2.cpu())
    topo.add_node("N 2 6", computing_resource=TOPO_CONFIG2.cpu())
    topo.add_node("N 2 7", computing_resource=TOPO_CONFIG2.cpu())
    topo.add_node("N 2 8", computing_resource=TOPO_CONFIG2.cpu())

    topo.add_edge("L1 S 1", "L2 S 1 1", bandwidth=10000, latency=TOPO_CONFIG2.latency())
    topo.add_edge("L1 S 1", "L2 S 2 2", bandwidth=10000, latency=TOPO_CONFIG2.latency())
    topo.add_edge("L1 S 2", "L2 S 1 2", bandwidth=10000, latency=TOPO_CONFIG2.latency())
    topo.add_edge("L1 S 2", "L2 S 2 1", bandwidth=10000, latency=TOPO_CONFIG2.latency())

    topo.add_edge("L2 S 1 1", "L2 S 1 3", bandwidth=10000, latency=TOPO_CONFIG2.latency())
    topo.add_edge("L2 S 1 1", "L2 S 1 4", bandwidth=10000, latency=TOPO_CONFIG2.latency())
    topo.add_edge("L2 S 1 2", "L2 S 1 3", bandwidth=10000, latency=TOPO_CONFIG2.latency())
    topo.add_edge("L2 S 1 2", "L2 S 1 4", bandwidth=10000, latency=TOPO_CONFIG2.latency())

    topo.add_edge("L2 S 2 1", "L2 S 2 3", bandwidth=1000, latency=TOPO_CONFIG2.latency())
    topo.add_edge("L2 S 2 1", "L2 S 2 4", bandwidth=1000, latency=TOPO_CONFIG2.latency())
    topo.add_edge("L2 S 2 2", "L2 S 2 3", bandwidth=1000, latency=TOPO_CONFIG2.latency())
    topo.add_edge("L2 S 2 2", "L2 S 2 4", bandwidth=1000, latency=TOPO_CONFIG2.latency())

    topo.add_edge("L2 S 1 3", "N 1 1", bandwidth=1000, latency=TOPO_CONFIG2.latency())
    topo.add_edge("L2 S 1 3", "N 1 2", bandwidth=1000, latency=TOPO_CONFIG2.latency())
    topo.add_edge("L2 S 1 3", "N 1 3", bandwidth=1000, latency=TOPO_CONFIG2.latency())
    topo.add_edge("L2 S 1 3", "N 1 4", bandwidth=1000, latency=TOPO_CONFIG2.latency())
    topo.add_edge("L2 S 1 4", "N 1 5", bandwidth=1000, latency=TOPO_CONFIG2.latency())
    topo.add_edge("L2 S 1 4", "N 1 6", bandwidth=1000, latency=TOPO_CONFIG2.latency())
    topo.add_edge("L2 S 1 4", "N 1 7", bandwidth=1000, latency=TOPO_CONFIG2.latency())
    topo.add_edge("L2 S 1 4", "N 1 8", bandwidth=1000, latency=TOPO_CONFIG2.latency())
    topo.add_edge("L2 S 2 3", "N 2 1", bandwidth=1000, latency=TOPO_CONFIG2.latency())
    topo.add_edge("L2 S 2 3", "N 2 2", bandwidth=1000, latency=TOPO_CONFIG2.latency())
    topo.add_edge("L2 S 2 3", "N 2 3", bandwidth=1000, latency=TOPO_CONFIG2.latency())
    topo.add_edge("L2 S 2 3", "N 2 4", bandwidth=1000, latency=TOPO_CONFIG2.latency())
    topo.add_edge("L2 S 2 4", "N 2 5", bandwidth=1000, latency=TOPO_CONFIG2.latency())
    topo.add_edge("L2 S 2 4", "N 2 6", bandwidth=1000, latency=TOPO_CONFIG2.latency())
    topo.add_edge("L2 S 2 4", "N 2 7", bandwidth=1000, latency=TOPO_CONFIG2.latency())
    topo.add_edge("L2 S 2 4", "N 2 8", bandwidth=1000, latency=TOPO_CONFIG2.latency())

    topo.name = 'data center'

    return topo

def Bcube_topo(k=0, n=4):
    """Standard Bcube topology
    k: layers
    n: num of servers
    total n ^ (k+1) servers
    """
    topo = nx.Graph()
    num_of_servers = n ** (k+1)
    # add server first
    for i in range(num_of_servers):
        topo.add_node("Server " + str(i), computing_resource=TOPO_CONFIG2.cpu())

    # add switch by layer
    num_of_switches = int(num_of_servers / n)
    for i in range(k+1):
        index_interval = n ** i
        num_of_one_group_switches = n ** i
        for j in range(num_of_switches):
            topo.add_node("Layer " + str(i) + "Switch " + str(j), computing_resource=0)
            start_index_server = j % num_of_one_group_switches + (j // num_of_one_group_switches) * num_of_one_group_switches * n
            for k in range(n):
                server_index = start_index_server + k * index_interval
                topo.add_edge("Server " + str(server_index), "Layer " + str(i) + "Switch " + str(j), bandwidth=1000, latency=TOPO_CONFIG2.latency())

    topo.name = 'Bcube'

    return topo