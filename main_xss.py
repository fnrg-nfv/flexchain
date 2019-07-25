#!/usr/bin/python3
from para_placement.topology import *
from para_placement.model import generate_vnf_set
import time
import matplotlib.pyplot as plt
import networkx as nx


def main():
    # print("Placement Main")
    # # model = generate_model(32, 100)
    # # model.save(file_name="model_data.pkl")
    # # model = Model.load(file_name="model_data.pkl")

    # # model.save(file_name="solved_model.pkl")
    # model = Model.load(file_name="model_data.pkl")
    # # model.draw_topo()

    # # print(model)
    # start_time = time.time()
    # greedy(model)
    # end_time = time.time()
    # print("Total execution time:", end_time - start_time)
    # vnf_list = generate_vnf_list()
    # for item in vnf_list:
    #     print(item)
    # topo = fat_tree_topo(n=6)
    topo = vl2_topo()
    nx.draw(topo, with_labels=True)
    plt.show()


if __name__ == '__main__':
    main()
