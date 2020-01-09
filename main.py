#!/usr/bin/python3
from para_placement import topology
from para_placement.helper import *
from para_placement.solution import *
from ttictoc import tic, toc


def create_testcase():
    # topo = topology.vl2_topo(
    #     port_num_of_aggregation_switch=8, port_num_of_tor_for_server=6)
    # topo = topology.fat_tree_topo(n=7)
    topo = topology.b_cube_topo(k=2)

    vnf_set = generate_vnf_set(size=30)

    model = Model(topo, generate_sfc_list2(
        topo=topo, vnf_set=vnf_set, size=400, base_idx=0))
    for idx, sfc in enumerate(model.sfc_list):
        print(idx, sfc)
    model.draw_topo()

    save_obj(model, "testcase/bcube_2")


def main():
    Configuration.para = True
    config.GC_BFS = True

    model = load_file("testcase/bcube_2")
    model.sfc_list = model.sfc_list[:200]
    model.draw_topo()

    result = {}

    model.clear()
    config.K = 1024
    result['optimal'] = linear_programming(model)
    result['RORP'] = rorp(model)
    model.clear()
    result['greedy para'] = greedy_para(model)
    print_dict_result(result, model)


if __name__ == '__main__':
    with TicToc("test"):
        create_testcase()
