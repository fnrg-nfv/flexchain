#!/usr/bin/python3
from para_placement import topology
from para_placement.helper import *
from para_placement.solution import *
from ttictoc import tic, toc


def main():
    Configuration.para = True
    config.GC_BFS = False
    config.K = 1024

    models = []

    vnf_set = generate_vnf_set(size=30)
    for i in [10]:
        topo = topology.vl2_topo(
            port_num_of_aggregation_switch=i, port_num_of_tor_for_server=i)
        model = Model(topo, generate_sfc_list2(
            topo=topo, vnf_set=vnf_set, size=600, base_idx=0))
        model.sfc_list = model.sfc_list[:2 * len(model.servers())]
        models.append(model)

    greedy_results = {}

    for model in models:
        result = {}
        model.clear()
        tic()
        result['greedy'] = PARC(model)
        result['greedy time'] = toc()

        print_dict_result(result, model)
        greedy_results[len(model.servers())] = result

    save_obj(greedy_results, "./results/time/greedy_{}".format(current_time()))

    rorp_results = {}
    for model in models:
        result = {}
        model.clear()
        tic()
        result['optimal'] = linear_programming(model)
        result['RORP'] = ROR(model)
        result['RORP time'] = toc()

        print_dict_result(result, model) 
        rorp_results[len(model.servers())] = result

    save_obj(rorp_results, "./results/time/rorp_{}".format(current_time()))


if __name__ == '__main__':
    with Timer(verbose_msg=f'[test] Elapsed time: {{}}'):
        main()
