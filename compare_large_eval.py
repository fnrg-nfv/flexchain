#!/usr/bin/python3
from para_placement import topology
from para_placement.helper import *
from para_placement.solution import *
from ttictoc import tic, toc
from compare_eval import compare_eval


def main():
    config.GC_BFS = False
    # model = load_file("testcase/compare_large")
    model = load_file("testcase/vl2_16_4")
    origin_sfc_list = model.sfc_list
    model.draw_topo()

    sizes = [20 * (i + 1) for i in range(10)]

    result = {}

    for size in sizes:
        model.sfc_list = origin_sfc_list[:size]
        result[size] = compare_eval(model)

    save_obj(result, "./results/compare/large_total_{}".format(current_time()))


if __name__ == '__main__':
    with Timer(verbose_msg=f'[time][{time.time()}] Elapsed time: {{}}'):
        main()
