import random

TOPO_CONFIG = {
    'CPU_LO': 4000,
    'CPU_HI': 8000,
    'BW_LO': 500,
    'BW_HI': 5000,
    'LT_LO': 0.05,
    'LT_HI': 0.05,
}

TOPO_CONFIG2 = lambda: None
# TOPO_CONFIG2.latency = lambda: random.uniform(0.1, 0.3)
TOPO_CONFIG2.latency = lambda: 0.05
TOPO_CONFIG2.bandwidth = lambda: 1000
TOPO_CONFIG2.cpu = lambda: random.randint(4000, 8000)

SFC_CONFIG = {
    'VNF_LO': 3,
    'VNF_HI': 6,

    # Requirement
    'TP_LO': 10,
    'TP_HI': 50,
    'LT_LO': 1,
    'LT_HI': 4,
}

NF_CONFIG = {
    'CPU_LO': 400,
    'CPU_HI': 800,
    'LT_LO': 0.045,
    'LT_HI': 0.3,
}

EPSILON = 0.33

K = 600

DC = True
DC_CHOOSING_SERVER = True

GREEDY_DFS = True
