#!/usr/bin/python3
from para_placement import topology
from para_placement.helper import *
from para_placement.solution import *
from ttictoc import tic, toc
import os


def main():
    # parameter init
    config.PARA = True
    config.GC_BFS = False
    config.ONE_MACHINE = False
    config.PARABOX_SIM = False

    # model init
    model = load_file("testcase/vl2")
    origin_sfc_list = model.sfc_list
    model.draw_topo()

    iter_times = 10
    unit = 40
    sizes = [unit * i + unit for i in range(iter_times)]
    result = {}
    temple_files = []

    for size in sizes:
        model.sfc_list = origin_sfc_list[:size]
        result[size] = iteration(model)
        temple_files.append(
            "./results/{}/{}_{}".format(model.topo.name, size, current_time()))
        save_obj(result[size], temple_files[-1])

    filename = "./results/{}/total_{}".format(model.topo.name, current_time())
    save_obj(result, filename)

    for temple_file in temple_files:
        os.remove(temple_file)


def iteration(model: Model):
    print("PLACEMENT MAIN")
    result = {}

    model.clear()
    result['heuristic'] = greedy_para(model)

    model.clear()
    config.K = 4096
    result['optimal'] = linear_programming(model)

    model.clear()
    config.K = 1024
    linear_programming(model)
    result['RORP'] = rorp(model)

    print_dict_result(result, model)
    return result


if __name__ == "__main__":
    with TicToc('test'):
        main()
