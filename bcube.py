#!/usr/bin/python3
from para_placement import topology
from para_placement.helper import *
from para_placement.solution import *
from ttictoc import tic, toc
import os


def main():
    # parameter init
    config.state = config.Setting.normal
    config.GC_BFS = True

    # model init
    model = load_file("testcase/bcube")
    origin_sfc_list = model.sfc_list
    model.draw_topo()

    sizes = [20 * (i + 1) for i in range(10)]
    result = {}
    temple_files = []

    sizes=[160]

    for size in sizes:
        model.sfc_list = origin_sfc_list[:size]
        result[size] = iteration(model)
        temple_files.append(
            "./results/{}/{}_{}".format(model.topo.name, size, current_time()))
        save_obj(result[size], temple_files[-1])

    filename = "./results/{}/total160_{}".format(model.topo.name, current_time())
    save_obj(result, filename)

    for temple_file in temple_files:
        os.remove(temple_file)


def iteration(model: Model):
    print("PLACEMENT MAIN")
    result = {}

    model.clear()
    result['heuristic'] = greedy_para(model)

    # model.clear()
    # config.K = 4096
    # result['optimal'] = linear_programming(model)

    model.clear()
    config.K = 1024
    result['optimal'] = linear_programming(model)
    # result['RORP'] = rorp(model)
    result['grp'] = rounding_to_integral(model, rounding_greedy)

    print_dict_result(result, model)
    return result


if __name__ == "__main__":
    with TicToc('test'):
        main()
