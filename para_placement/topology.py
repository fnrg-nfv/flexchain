import networkx as nx
import matplotlib.pyplot as plt
import random

import warnings
import matplotlib.cbook
import math

warnings.filterwarnings("ignore", category=matplotlib.cbook.mplDeprecation)
fig, ax = plt.subplots()
fig.set_tight_layout(False)


# random generate topo with 100 nodes
# node CPU capacity: 4000~8000 Mhz
# node connectivity: log(n) / n
# edge latency: 2~5 ms
# edge bandwidth: 1000~10000 Mbps todo

def generate_randomly(size: int = 100):
    topo = nx.Graph()
    for i in range(size):
        topo.add_node(i, computing_resource=random.randint(4000, 8000))

    connectivity = (math.log2(size) - 2) / size
    for i in range(size):
        for j in range(i + 1, size):
            if random.uniform(0, 1) < connectivity:
                topo.add_edge(i, j, bandwidth=random.randint(1000, 10000), latency=random.uniform(2, 5))

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
