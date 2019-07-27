#!/usr/bin/python3
from draw_plots import draw_plot
from para_placement import topology
from para_placement.helper import *
from para_placement.solution import *
import para_placement.config as config

topo_files = ['./gml_data/Cernet.gml', './gml_data/Geant2012.gml', './gml_data/Internetmci.gml']


def main():
    # parameter init
    Configuration.para = True
    config.DC_CHOOSING_SERVER = False

    # model init
    # topo = topology.fat_tree_topo(n=5)
    topo = topology.b_cube_topo(k=2)
    # topo = topology.vl2_topo(port_num_of_aggregation_switch=6, port_num_of_tor_for_server=4)
    vnf_set = generate_vnf_set(size=50)
    model = Model(topo, [])

    model.draw_topo()

    iter_times = 10
    unit = 40
    result = {}
    temple_files = []

    for i in range(iter_times):
        size = unit * i + unit
        model = Model(topo, generate_sfc_list(topo=topo, vnf_set=vnf_set, size=size, base_idx=0))
        result[size] = iteration(model)
        temple_files.append("result_{}_{}_{}.pkl".format(model.topo.name, size, current_time()))
        save_obj(result[size], temple_files[-1])

    filename = "result_{}_{}.pkl".format(model.topo.name, current_time())
    save_obj(result, filename)

    draw_plot(result, "result_{}_{}".format(model.topo.name, current_time()))

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
    topo = topology.fat_tree_topo(n=5)
    # topo = topology.b_cube_topo(k=2)
    # topo = topology.vl2_topo(port_num_of_aggregation_switch=6, port_num_of_tor_for_server=4)

    vnf_set = generate_vnf_set(size=30)
    sfc_size = 100
    model = Model(topo, generate_sfc_list2(topo, vnf_set, sfc_size))
    model.draw_topo(1)

    Configuration.para = True
    config.DC_CHOOSING_SERVER = False

    iteration(model)
    # linear_programming(model)
    # rounding_to_integral(model, rounding_method=rounding_one)
    #
    # model.clear()


def add(t1, t2):
    if type(t1) is not type(t2):
        return None

    if type(t1) is dict:
        ret = dict()
        for key in t1:
            ret[key] = add(t1[key], t2[key])
        return ret

    if type(t1) is tuple:
        length = min(len(t1), len(t2))
        ret = []
        for i in range(length):
            ret.append(add(t1[i], t2[i]))
        return tuple(ret)

    return t1 + t2


if __name__ == '__main__':
    main()
