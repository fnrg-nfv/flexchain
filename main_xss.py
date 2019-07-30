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
    # topo = vl2_topo()
    # nx.draw(topo, with_labels=True)
    # plt.show()
    x = [64, 128, 256, 512, 1024, 1500]
    y1 = [206, 214, 367, 398, 559, 755]
    y2 = [184, 194, 286, 302, 376, 441]
    
    plt.plot(x,y1,'s-',color = 'r',label="Copy")#s-:方形
    plt.plot(x,y2,'o-',color = 'g',label="Merge")#o-:圆形
    # plt.xticks( range(6), (64, 128, 256, 512, 1024, 1500) )
    plt.xlabel('Pakcet size (bytes)')
    plt.ylabel('Averge time overhead (ns)')
    plt.grid(linestyle='--')  # 显示网格
    plt.legend()
    plt.savefig('{}.eps'.format("parallel_overhead"), format='eps')
    plt.show()

if __name__ == '__main__':
    main()
