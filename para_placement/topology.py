import random
import warnings

import math
import matplotlib.cbook
import matplotlib.pyplot as plt
import networkx as nx

from para_placement.config import TOPO_CONFIG
from para_placement.helper import extract_filename


'''
node CPU capacity: 4000~8000 Mhz
node connectivity: log(n) / n
edge latency: 2~5 ms
edge bandwidth: 500~5000 Mbps todo
'''


# random generate topo with 100 nodes
def generate_randomly(size=100):
    topo = nx.Graph()
    for i in range(size):
        topo.add_node(i, computing_resource=TOPO_CONFIG.cpu())

    connectivity = (math.log2(size) - 2) / size
    for i in range(size):
        for j in range(i + 1, size):
            if random.uniform(0, 1) < connectivity:
                topo.add_edge(i, j, bandwidth=TOPO_CONFIG.bandwidth(),
                              latency=TOPO_CONFIG.latency())

    topo.name = 'random'

    return topo


def b_cube_topo(k=0, n=4):
    """Standard Bcube topology
    k: layers
    n: num of servers
    total n ^ (k+1) servers
    """
    topo = nx.Graph()
    num_of_servers = n ** (k + 1)
    # add server first
    for i in range(num_of_servers):
        topo.add_node("Server {}".format(
            i), computing_resource=TOPO_CONFIG.cpu())

    # add switch by layer
    num_of_switches = int(num_of_servers / n)
    for i in range(k + 1):
        index_interval = n ** i
        num_of_one_group_switches = n ** i
        for j in range(num_of_switches):
            topo.add_node("Layer {} Switch {}".format(
                i, j), computing_resource=0)
            start_index_server = j % num_of_one_group_switches + (
                j // num_of_one_group_switches) * num_of_one_group_switches * n
            for k in range(n):
                server_index = start_index_server + k * index_interval
                topo.add_edge("Server {}".format(server_index), "Layer {} Switch {}".format(i, j), bandwidth=TOPO_CONFIG.bandwidth(),
                              latency=TOPO_CONFIG.latency())

    topo.name = 'Bcube'

    return topo


def fat_tree_topo(n=4):
    """Standard fat tree topology
    n: number of pods
    total n^3/4 servers
    """
    topo = nx.Graph()
    num_of_servers_per_edge_switch = n // 2
    num_of_edge_switches = n // 2
    num_of_aggregation_switches = num_of_edge_switches
    num_of_core_switches = int((n / 2) * (n / 2))

    # generate topo pod by pod
    for i in range(n):
        for j in range(num_of_edge_switches):
            topo.add_node("Pod {} edge switch {}".format(
                i, j), computing_resource=0)
            topo.add_node("Pod {} aggregation switch {}".format(
                i, j), computing_resource=0)
            for k in range(num_of_servers_per_edge_switch):
                topo.add_node("Pod {} edge switch {} server {}".format(
                    i, j, k), computing_resource=TOPO_CONFIG.cpu())
                topo.add_edge("Pod {} edge switch {}".format(i, j), "Pod {} edge switch {} server {}".format(i, j, k),
                              bandwidth=1000, latency=TOPO_CONFIG.latency())

    # add edge among edge and aggregation switch within pod
    for i in range(n):
        for j in range(num_of_aggregation_switches):
            for k in range(num_of_edge_switches):
                topo.add_edge("Pod {} aggregation switch {}".format(i, j), "Pod {} edge switch {}".format(i, k),
                              bandwidth=1000, latency=TOPO_CONFIG.latency())

    # add edge among core and aggregation switch
    num_of_core_switches_connected_to_same_aggregation_switch = num_of_core_switches // num_of_aggregation_switches
    for i in range(num_of_core_switches):
        topo.add_node("Core switch {}".format(i), computing_resource=0)
        aggregation_switch_index_in_pod = i // num_of_core_switches_connected_to_same_aggregation_switch
        for j in range(n):
            topo.add_edge("Core switch {}".format(i),
                          "Pod {} aggregation switch {}".format(j, aggregation_switch_index_in_pod), bandwidth=1000,
                          latency=TOPO_CONFIG.latency())

    topo.name = 'fattree'

    return topo


def vl2_topo(port_num_of_aggregation_switch=4, port_num_of_tor_for_server=2):
    """Standard vl2 topology
    total port_num_of_aggregation_switch^2 / 4 * port_num_of_tor_for_server servers
    """
    topo = nx.Graph()
    num_of_aggregation_switches = port_num_of_aggregation_switch
    num_of_intermediate_switches = num_of_aggregation_switches // 2
    num_of_tor_switches = (port_num_of_aggregation_switch //
                           2) * (port_num_of_aggregation_switch // 2)

    # create intermediate switch
    for i in range(num_of_intermediate_switches):
        topo.add_node("Intermediate switch {}".format(i), computing_resource=0)

    # create aggregation switch
    for i in range(num_of_aggregation_switches):
        topo.add_node("Aggregation switch {}".format(i), computing_resource=0)
        for j in range(num_of_intermediate_switches):
            topo.add_edge("Aggregation switch {}".format(i), "Intermediate switch {}".format(j), bandwidth=1000,
                          latency=TOPO_CONFIG.latency())

    # create ToR switch
    num_of_tor_switches_per_aggregation_switch_can_connect = num_of_aggregation_switches // 2
    for i in range(num_of_tor_switches):
        topo.add_node("ToR switch {}".format(i), computing_resource=0)
        # every ToR only need to connect 2 aggregation switch
        aggregation_index = (
            i // num_of_tor_switches_per_aggregation_switch_can_connect) * 2
        topo.add_edge("ToR switch {}".format(i), "Aggregation switch {}".format(aggregation_index), bandwidth=1000,
                      latency=TOPO_CONFIG.latency())
        aggregation_index += 1  # The second aggregation switch
        topo.add_edge("ToR switch {}".format(i), "Aggregation switch {}".format(aggregation_index), bandwidth=1000,
                      latency=TOPO_CONFIG.latency())
        # add server to ToR
        for j in range(port_num_of_tor_for_server):
            topo.add_node("ToR switch {} server {}".format(i, j),
                          computing_resource=TOPO_CONFIG.cpu())
            topo.add_edge("ToR switch {} server {}".format(i, j), "ToR switch {}".format(i), bandwidth=1000,
                          latency=TOPO_CONFIG.latency())

    topo.name = 'VL2'

    return topo
