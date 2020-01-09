import random


def TOPO_CONFIG(): return None


# TOPO_CONFIG.latency = lambda: 0.05 # ok
TOPO_CONFIG.latency = lambda: 0.001
TOPO_CONFIG.bandwidth = lambda: 10000  # ok not write no source
TOPO_CONFIG.cpu = lambda: random.randint(4000, 8000)  # ok not write


def SFC_CONFIG(): return None


SFC_CONFIG.size = lambda: random.randint(3, 7)  # ok
# required throuphput
SFC_CONFIG.r_throughput = lambda: min(max(random.gauss(100, 50), 10), 200)
# required latency
SFC_CONFIG.r_latency = lambda: random.uniform(1.0, 3.0)

# vnf cpu overhead
SFC_CONFIG.vnf_cpu = lambda: random.randint(1000, 2000)  # no source not write
# vnf latency overhead
SFC_CONFIG.vnf_latency = lambda: random.uniform(0.045, 0.3)  # ok

K = 8000
K_MIN = 128

PARA = True

ONE_MACHINE = False

GC_BFS = False
