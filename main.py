#!/usr/bin/python3
from para_placement import topology
from para_placement.helper import *
from para_placement.solution import *
from ttictoc import tic, toc


def create_test_case():
    topo = topology.vl2_topo(
        port_num_of_aggregation_switch=8, port_num_of_tor_for_server=6)
    vnf_set = generate_vnf_set(size=30)

    model = Model(topo, generate_sfc_list2(
        topo=topo, vnf_set=vnf_set, size=400, base_idx=0))
    model.draw_topo()

    save_obj(model, "testcase/vl2_8_6_400")


def single_test():
    Configuration.para = True

    model = load_file("testcase/vl2_400")
    model.sfc_list = model.sfc_list[:200]
    # model.draw_topo()

    result = {}

    model.clear()
    config.K = 1024
    result['optimal'] = linear_programming(model)

    result['greedy para'] = greedy_para(model)

    print_dict_result(result, model)

    save_obj(result, "results/k/baseline_{}".format(current_time()))


def k_experiment():
    Configuration.para = True

    model = load_file("testcase/vl2_400")
    model.sfc_list = model.sfc_list[:200]
    # model.draw_topo()

    results = {}

    # k_list = [32, 64, 128, 256, 512, 1024, 2048, 4096]
    k_list = [250, 500, 750, 1000, 1250, 1500, 1750, 2000]
    config.K_MIN = 128

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
        save_obj(result, "results/k/k={}_{}".format(k, current_time()))
        results[k] = result

    save_obj(results, "results/k/total_{}".format(current_time()))


def print_dict_result(result, model):
    print("\n>>>>>>>>>>>>>>>>>> Result Summary <<<<<<<<<<<<<<<<<<")
    print("{}\n".format(model))
    for key in result:
        print("{}: {}".format(key, result[key]))


def first_experience():
    # parameter init
    Configuration.para = True

    # model init
    topo = topology.fat_tree_topo(n=6)
    # topo = topology.b_cube_topo(k=2)
    # topo = topology.vl2_topo(port_num_of_aggregation_switch=6, port_num_of_tor_for_server=4)
    vnf_set = generate_vnf_set(size=30)
    model = Model(topo, [])

    model.draw_topo()

    iter_times = 10
    unit = 40
    result = {}
    temple_files = []
    sizes = [unit * i + unit for i in range(iter_times)]

    for size in sizes:
        model = Model(topo, generate_sfc_list2(
            topo=topo, vnf_set=vnf_set, size=size, base_idx=0))
        result[size] = iteration(model)
        temple_files.append(
            "./results/{}/{}_{}.pkl".format(model.topo.name, size, current_time()))
        save_obj(result[size], temple_files[-1])

    filename = "./results/{}/{}.pkl".format(model.topo.name, current_time())
    save_obj(result, filename)

    for temple_file in temple_files:
        os.remove(temple_file)


@print_run_time
def iteration(model: Model):
    print("PLACEMENT MAIN")
    config.K = 8000
    ret = dict()

    model.clear()
    ret['greedy'] = greedy_dc(model)

    model.clear()
    ret['optimal'] = linear_programming(model)
    ret['heuristic'] = rounding_to_integral(
        model, rounding_method=rounding_one)

    print_dict_result(ret)

    return ret


@print_run_time
def compare_experience(model: Model, init_k=4000):
    print("PLACEMENT MAIN")
    ret = dict()

    model.clear()
    config.K = init_k
    Configuration.para = True
    config.ONE_MACHINE = False
    linear_programming(model)
    ret['heuristic'] = rounding_to_integral(
        model, rounding_method=rounding_one)

    model.clear()
    config.K = init_k
    Configuration.para = False
    config.ONE_MACHINE = False
    linear_programming(model)
    ret['PWOP'] = rounding_to_integral(model, rounding_method=rounding_one)

    model.clear()
    config.K = init_k
    Configuration.para = True
    config.ONE_MACHINE = True
    linear_programming(model)
    ret['PWPOM'] = rounding_to_integral(model, rounding_method=rounding_one)

    print_dict_result(ret)

    return ret


def main_compare():
    # model init
    topo = topology.b_cube_topo(k=2)
    vnf_set = generate_vnf_set(size=30)
    sizes = [20 * (i + 1) for i in range(10)]
    # sizes = [100, 120, 140]

    result = dict()

    for size in sizes:
        model = Model(topo, generate_sfc_list2(topo, vnf_set, size, 0))
        model.draw_topo()
        result[size] = compare_experience(model)

        save_obj(result[size], "./results/compare/{}_{}_{}.pkl".format(
            model.topo.name, size, current_time()))

    save_obj(result, "./results/compare/{}_{}.pkl".format(topo.name, current_time()))


if __name__ == '__main__':
    with TicToc("test"):
        k_experiment()
