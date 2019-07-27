#!/usr/bin/python3
import winsound

from para_placement import topology
from para_placement.helper import *
from para_placement.solution import *

topo_files = ['./gml_data/Cernet.gml', './gml_data/Geant2012.gml', './gml_data/Internetmci.gml']


def main():
    # parameter init
    Configuration.para = True
    config.DC_CHOOSING_SERVER = False

    # model init
    topo = topology.fat_tree_topo(n=6)
    # topo = topology.b_cube_topo(k=2)
    # topo = topology.vl2_topo(port_num_of_aggregation_switch=6, port_num_of_tor_for_server=4)
    vnf_set = generate_vnf_set(size=50)
    model = Model(topo, [])

    model.draw_topo()

    iter_times = 10
    unit = 40
    dup_times = 5
    result = {}
    temple_files = []

    for i in range(iter_times):
        size = unit * i + unit
        # result[size] = []
        # for _ in range(dup_times):
        #     model = Model(topo, generate_sfc_list(topo=topo, vnf_set=vnf_set, size=size, base_idx=0))
        #     cur_result = iteration(model)
        #     temple_files.append("result_{}_{}_{}.pkl".format(model.topo.name, size, current_time()))
        #     save_obj(cur_result, temple_files[-1])
        #     result[size].append(cur_result)
        model = Model(topo, generate_sfc_list(topo=topo, vnf_set=vnf_set, size=size, base_idx=0))
        result[size] = iteration(model)
        temple_files.append("result_{}_{}_{}.pkl".format(model.topo.name, size, current_time()))
        save_obj(result[size], temple_files[-1])

    filename = "result_{}_{}.pkl".format(model.topo.name, current_time())
    save_obj(result, filename)

    # draw_plot(result, "result_{}_{}".format(model.topo.name, current_time()))

    for temple_file in temple_files:
        os.remove(temple_file)


@print_run_time
def iteration(model: Model):
    print("PLACEMENT MAIN")
    ret = dict()

    model.clear()
    ret['greedy'] = greedy_dc(model)

    # model.clear()
    # ret['greedy 2'] = greedy2(model)

    model.clear()
    ret['optimal'] = linear_programming(model)
    # filename = "solved_model_{}.pkl".format(uuid.uuid4())
    # model.save(filename)
    # ret['ILP greedy'] = rounding_to_integral(model, rounding_method=rounding_greedy)
    #
    # model = Model.load(filename)
    ret['heuristic'] = rounding_to_integral(model, rounding_method=rounding_one)
    # os.remove(filename)

    print("\n>>>>>>>>>>>>>>>>>> Result Summary <<<<<<<<<<<<<<<<<<")
    print("Para: {}\t{}\n".format(Configuration.para, model))
    for key in ret:
        print("{}: {}".format(key, ret[key]))

    return ret


def main_dc():
    # topo = topology.fat_tree_topo(n=6)
    # topo = topology.b_cube_topo(k=2)
    topo = topology.vl2_topo(port_num_of_aggregation_switch=6, port_num_of_tor_for_server=4)

    vnf_set = generate_vnf_set(size=30)
    sfc_size = 400
    model = Model(topo, generate_sfc_list2(topo, vnf_set, sfc_size))
    model.draw_topo()

    Configuration.para = True
    config.DC_CHOOSING_SERVER = False

    result = iteration(model)

    # greedy_dc(model)
    # config.GREEDY_DFS = False
    # model.clear()
    # greedy_dc(model)
    # model.clear()
    # linear_programming(model)
    # rounding_to_integral(model, rounding_method=rounding_one)
    # model.print_resource_usages()

    filename = "result_{}_{}_{}.pkl".format(model.topo.name, sfc_size, current_time())
    save_obj(result, filename)


def alert(duration=1000, freq=440):
    winsound.Beep(freq, duration)


if __name__ == '__main__':
    main()
    alert()
