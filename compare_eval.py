#!/usr/bin/python3
from para_placement import topology
from para_placement.helper import *
from para_placement.solution import *
from ttictoc import tic, toc


@print_run_time
def compare_eval(model: Model, k=512):
    print("PLACEMENT MAIN")
    result = dict()

    model.clear()
    config.K = k
    config.PARA = True
    config.ONE_MACHINE = False
    result['optimal'] = linear_programming(model)
    result['RORP'] = rorp(model)

    model.clear()
    config.K = k
    config.PARA = False
    config.ONE_MACHINE = False
    linear_programming(model)
    result['NP'] = rorp(model)

    model.clear()
    config.K = k
    config.PARA = True
    config.ONE_MACHINE = True
    linear_programming(model)
    result['OM'] = rorp(model)

    print_dict_result(result, model)

    return result


def main():
    config.GC_BFS = False
    model = load_file("testcase/compare")
    origin_sfc_list = model.sfc_list
    model.draw_topo()

    sizes = [20 * (i + 1) for i in range(10)]

    result = {}

    for size in sizes:
        model.sfc_list = origin_sfc_list[:size]
        result[size] = compare_eval(model)

    save_obj(result, "./results/compare/total_{}".format(current_time()))


if __name__ == '__main__':
    with TicToc("test"):
        main()
