#!/usr/bin/python3
from para_placement import topology
from para_placement.helper import *
from para_placement.solution import *
from ttictoc import tic, toc


@print_run_time
def compare_eval(model: Model, k=256):
    print("PLACEMENT MAIN")
    result = dict()

    model.clear()
    config.state = config.Setting.flexchain
    result['heuristic'] = greedy_para(model)

    model.clear()
    config.state = config.Setting.no_para
    result['Chain w/o parallelism'] = greedy_dc(model)

    model.clear()
    config.state = config.Setting.nfp_naive
    result['NFP-naïve'] = greedy_dc(model)

    model.clear()
    config.state = config.Setting.parabox_naive
    result['PARABOX-naïve'] = greedy_dc(model)

    print_dict_result(result, model)

    return result


def main():
    config.GC_BFS = False
    config.K_MIN = 64
    model = load_file("testcase/vl2_16_4")
    origin_sfc_list = model.sfc_list

    sizes = [30 * (i + 1) for i in range(10)]

    result = {}

    for size in sizes:
        model.sfc_list = origin_sfc_list[:size]
        result[size] = compare_eval(model)

    save_obj(result, "./results/compare/total_{}".format(current_time()))


if __name__ == '__main__':
    with Timer(verbose_msg=f'[test] Elapsed time: {{}}'):
        main()
