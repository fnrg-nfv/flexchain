import random

TOPO_CONFIG = {
    'CPU_LO': 4000,
    'CPU_HI': 8000,
    'BW_LO': 500,
    'BW_HI': 5000,
    # 'LT_LO': 2,
    # 'LT_HI': 5,
    'LT_LO': 0.15,
    'LT_HI': 0.3,
}

TOPO_CONFIG2 = lambda: None
# TOPO_CONFIG2.latency = lambda: random.uniform(0.1, 0.3)
TOPO_CONFIG2.latency = lambda: 0.05
TOPO_CONFIG2.bandwidth = lambda: random.randint(500, 5000)
TOPO_CONFIG2.cpu = lambda: random.randint(4000, 8000)

SFC_CONFIG = {
    'VNF_LO': 2,
    'VNF_HI': 5,

    # Requirement
    'TP_LO': 50,
    'TP_HI': 500,
    # 'LT_LO': 10,
    # 'LT_HI': 30,
    'LT_LO': 1,
    'LT_HI': 2,
}

NF_CONFIG = {
    'CPU_LO': 800,
    'CPU_HI': 1600,
    # 'LT_LO': 0.2,
    # 'LT_HI': 2,
    'LT_LO': 0.045,
    'LT_HI': 0.3,
}

EPSILON = 0.33

if __name__ == '__main__':
    print(TOPO_CONFIG2.latency())
