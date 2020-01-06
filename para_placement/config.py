import random


def TOPO_CONFIG(): return None


TOPO_CONFIG.latency = lambda: 0.05 # ok
TOPO_CONFIG.bandwidth = lambda: 1000 # ok not write no source
TOPO_CONFIG.cpu = lambda: random.randint(4000, 8000) # ok not write


def SFC_CONFIG(): return None


SFC_CONFIG.size = lambda: random.randint(3, 7) # ok
# required throuphput
SFC_CONFIG.r_throughput = lambda: random.randint(10, 20)
# required latency
SFC_CONFIG.r_latency = lambda: random.uniform(0.5, 2)

# vnf cpu overhead
SFC_CONFIG.vnf_cpu = lambda: random.randint(1000, 2000) # no source not write
# vnf latency overhead
SFC_CONFIG.vnf_latency = lambda: random.uniform(0.045, 0.3) # ok

K = 600
# K = 300

DC = True
DC_CHOOSING_SERVER = True

GREEDY_DFS = True

ONE_MACHINE = False
