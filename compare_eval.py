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
    config.K = k
    config.PARA = True
    config.ONE_MACHINE = False
    config.PARABOX_SIM = False
    result['optimal'] = linear_programming(model)
    result['RORP'] = rorp(model)

    model.clear()
    config.K = k
    config.PARA = False
    config.ONE_MACHINE = False
    config.PARABOX_SIM = False
    linear_programming(model)
    result['NP'] = rorp(model)

    model.clear()
    config.K = k
    config.PARA = True
    config.ONE_MACHINE = True
    config.PARABOX_SIM = False
    linear_programming(model)
    result['OM'] = rorp(model)

    model.clear()
    config.K = k
    config.PARA = True
    config.ONE_MACHINE = False
    config.PARABOX_SIM = True
    linear_programming(model)
    result['PB'] = rorp(model)

    print_dict_result(result, model)

    return result


def main():
    config.GC_BFS = False
    config.K_MIN = 128
    model = load_file("testcase/vl2")
    origin_sfc_list = model.sfc_list

    sizes = [20 * (i + 1) for i in range(10)]

    sizes = [60, 120, 200]

    result = {}

    for size in sizes:
        model.sfc_list = origin_sfc_list[:size]
        result[size] = compare_eval(model)

    # save_obj(result, "./results/compare/total_{}".format(current_time()))


if __name__ == '__main__':
    with TicToc("test"):
        main()
