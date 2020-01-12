#!/usr/bin/python3
from para_placement import topology
from para_placement.helper import *
from para_placement.solution import *
from ttictoc import tic, toc


def create_testcase():
    vl2_topo = topology.vl2_topo(
        port_num_of_aggregation_switch=8, port_num_of_tor_for_server=6)
    fattree_topo = topology.fat_tree_topo(n=7)
    bcube_topo = topology.b_cube_topo(k=2)

    vnf_set = generate_vnf_set(size=30)

    vl2_model = Model(vl2_topo, generate_sfc_list2(
        topo=vl2_topo, vnf_set=vnf_set, size=500, base_idx=0))
    fattree_model = Model(fattree_topo, generate_sfc_list2(
        topo=fattree_topo, vnf_set=vnf_set, size=500, base_idx=0))
    bcube_model = Model(bcube_topo, generate_sfc_list2(
        topo=bcube_topo, vnf_set=vnf_set, size=500, base_idx=0))

    save_obj(vl2_model, "testcase/vl2")
    save_obj(fattree_model, "testcase/fattree")
    save_obj(bcube_model, "testcase/bcube")


if __name__ == '__main__':
    with TicToc("test"):
        create_testcase()
