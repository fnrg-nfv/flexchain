#!/usr/bin/python3
from para_placement.helper import *
from para_placement.solution import *


def main():
    # parameter init
    config.state = config.Setting.flexchain
    config.GC_BFS = False

    # algorithms = ['PARC']
    # algorithms = ['ROR']
    algorithms = ['PARC', 'ROR']

    # model init
    model = load_file("testcase/vl2")
    origin_sfc_list = model.sfc_list
    model.draw_topo()

    total_size = 200
    batch_sizes = [1, 10, 40]
    result = {}

    for alg in algorithms:
        result[alg] = {}
        for batch_size in batch_sizes:
            result[alg][batch_size] = {}
            model.clear()
            cur = Model(copy.deepcopy(model.topo), [])
            for i in range(0, total_size, batch_size):
                cur.sfc_list = origin_sfc_list[i:i + batch_size]
                result[alg][batch_size][i] = iteration(cur, alg)
                cur = cur.reduce()

    print_dict_result(result, model)
    save_obj(result, "./results/online/{}".format(current_time()))


def iteration(model: Model, algorithm):
    if algorithm == 'PARC':
        return PARC(model)[0]
    elif algorithm == 'ROR':
        config.K = 1024
        linear_programming(model)
        return ROR(model)[0]
    return 0


if __name__ == "__main__":
    with Timer(verbose_msg=f'[test] Elapsed time: {{}}'):
        main()
