
#!/usr/bin/python3
from para_placement import topology
from para_placement.helper import *
from para_placement.solution import *
from ttictoc import tic, toc
import os

def main():
    size = 30
    vnf_set = generate_vnf_set(size=size)
    pairs = 0
    para_num = 0
    for i in range(size):
        for j in range(i + 1, size):
            pairs += 1
            if vnf_set[i].parallelizable_analysis(vnf_set[j]) >= 0:
                para_num += 1
    print(para_num, pairs, para_num/pairs)

def main2():
    # parameter init
    config.state = config.Setting.normal
    config.GC_BFS = False

    # model init
    model = load_file("testcase/vl2")
    origin_sfc_list = model.sfc_list
    model.draw_topo()

    sizes = [20 * (i + 1) for i in range(10)]
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

    # model.clear()
    # result['heuristic'] = greedy_para(model)

    model.clear()
    config.K = 4096
    result['optimal'] = linear_programming(model)

    # model.clear()
    # config.K = 1024
    # linear_programming(model)
    # result['RORP'] = rorp(model)

    print_dict_result(result, model)
    return result


if __name__ == "__main__":
    with Timer(verbose_msg=f'[test] Elapsed time: {{}}'):
        main()
