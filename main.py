#!/usr/bin/python3
from para_placement import topology
from para_placement.helper import *
from para_placement.solution import *
from ttictoc import tic, toc


def create_testcase():
    vl2_topo = topology.vl2_topo(
        port_num_of_aggregation_switch=16, port_num_of_tor_for_server=4)
    fattree_topo = topology.fat_tree_topo(n=7)
    bcube_topo = topology.b_cube_topo(k=2)

    vnf_set = generate_vnf_set(size=30)

    vl2_model = Model(vl2_topo, generate_sfc_list2(
        topo=vl2_topo, vnf_set=vnf_set, size=600, base_idx=0))
    fattree_model = Model(fattree_topo, generate_sfc_list2(
        topo=fattree_topo, vnf_set=vnf_set, size=500, base_idx=0))
    bcube_model = Model(bcube_topo, generate_sfc_list2(
        topo=bcube_topo, vnf_set=vnf_set, size=500, base_idx=0))

    vl2_model.draw_topo()

    save_obj(vl2_model, "testcase/vl2_16_4")
    # save_obj(fattree_model, "testcase/fattree")
    # save_obj(bcube_model, "testcase/bcube")


def _tp_parabox(cut, strategy):
    ret = 0
    cut += 1
    strategy.append(0)
    strategy.append(0)
    strategy.insert(0, 0)
    for i in range(0, cut + 1):
        next = False
        for j in range(i, len(strategy)):
            if not next:
                if strategy[j] == 0:
                    next = True
            else:
                if j > cut:
                    ret += 1
                if strategy[j] == 0:
                    break
        if not next:
            ret += 1
    return ret


if __name__ == '__main__':
    vl2_topo = topology.vl2_topo(
        port_num_of_aggregation_switch=16, port_num_of_tor_for_server=4)
    vnf_set = generate_vnf_set(size=30)
    vnf_list = []
    for j in range(7):
        vnf_list.append(random.choice(vnf_set))
    print(time())
    ParaAnalyzer(vnf_list)
    print(time())
