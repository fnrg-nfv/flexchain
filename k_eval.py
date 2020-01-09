#!/usr/bin/python3
from para_placement import topology
from para_placement.helper import *
from para_placement.solution import *
from ttictoc import tic, toc


def main():
    Configuration.para = True

    model = load_file("testcase/vl2_8_6")
    model.sfc_list = model.sfc_list[:200]

    results = {}

    k_list = [64, 128, 256, 512, 768, 1024, 1280, 1536, 1792, 2048, 4096]
    config.K_MIN = 32

    for k in k_list:
        result = {}
        config.K = k
        print('k =', k)
        model.clear()

        tic()
        result['optimal'] = linear_programming(model)
        result['RORP'] = rorp(model)
        result['RORP time'] = toc()
        model.clear()
        result['greedy'] = greedy_para(model)
        print_dict_result(result, model)
        results[k] = result

    save_obj(results, "results/k/total_{}".format(current_time()))


if __name__ == "__main__":
    with TicToc('test'):
        main()
