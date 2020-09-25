# !/usr/bin/python3
import numpy

from para_placement import topology
from para_placement.helper import *
from para_placement.solution import *


def main():
    config.state = config.Setting.flexchain
    config.GC_BFS = False

    size = 30
    vnf_set = generate_vnf_set_with_para_prob(size=size, prob=0)
    vl2_topo = topology.vl2_topo(
        port_num_of_aggregation_switch=8, port_num_of_tor_for_server=6)
    vl2_model = Model(vl2_topo, generate_sfc_list2(
        topo=vl2_topo, vnf_set=vnf_set, size=100, base_idx=0))
    vl2_model.draw_topo()

    result = dict()
    step = .2
    for prob in numpy.arange(0, 1.1, step):
        print("Parallelism Probability:", prob)
        vl2_model.print_sfc_list_feature()
        result[prob] = iteration(model=vl2_model)
        update_vnf_set_with_para_prob(vnf_set, step)
        for sfc in vl2_model.sfc_list:
            sfc.pa = ParaAnalyzer(sfc.vnf_list)

    print_dict_result(result, vl2_model)

    filename = "./results/para_prob/{}".format(current_time())
    save_obj(result, filename)


def iteration(model: Model):
    print("PLACEMENT MAIN")
    result = {}

    model.clear()
    result['heuristic'] = PARC(model)

    config.K = 256
    model.clear()
    linear_programming(model)
    result['RORP'] = ROR(model)

    return result


if __name__ == "__main__":
    with Timer(verbose_msg=f'[test] Elapsed time: {{}}'):
        main()
