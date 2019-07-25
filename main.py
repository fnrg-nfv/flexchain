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
    gml_filename = topo_files[0]

    # model init
    topo = topology.parse_gml(gml_filename)
    vnf_set = generate_vnf_set(size=50)
    model = Model(topo, [])

    model.draw_topo()

    iter_times = 10
    unit = 50
    result = {}
    temple_files = []

    for i in range(iter_times):
        model.clear()
        model.sfc_list.extend(generate_sfc_list(topo=topo, vnf_set=vnf_set, size=unit, base_idx=i * unit))
        size = unit * i + unit
        result[size] = iteration(model)
        temple_files.append("result_{}_{}_{}.pkl".format(extract_str(gml_filename), size, current_time()))
        save_obj(result[size], temple_files[-1])

    filename = "result_{}_{}.pkl".format(extract_str(gml_filename), current_time())
    print(filename)
    save_obj(result, filename)

    draw_plot(result, "result_{}_{}".format(extract_str(gml_filename), current_time()))

    for temple_file in temple_files:
        os.remove(temple_file)


@print_run_time
def iteration(model: Model):
    print("PLACEMENT MAIN")
    ret = dict()

    model.clear()
    ret['greedy'] = greedy(model)

    # model.clear()
    # ret['greedy 2'] = greedy2(model)

    model.clear()
    ret['optimal'] = linear_programming(model)
    # filename = "solved_model_{}.pkl".format(uuid.uuid4())
    # model.save(filename)
    # ret['ILP greedy'] = rounding_to_integral(model, rounding_method=rounding_greedy)
    #
    # model = Model.load(filename)
    ret['ILP one'] = rounding_to_integral(model, rounding_method=rounding_one)
    # os.remove(filename)

    print("\n>>>>>>>>>>>>>>>>>> Result Summary <<<<<<<<<<<<<<<<<<")
    print("Para: {}\t{}\n".format(Configuration.para, model))
    for key in ret:
        print("{}: {}".format(key, ret[key]))

    return ret


def main_single():
    filename = topo_files[1]

    # model init
    topo = topology.parse_gml(filename)
    vnf_set = generate_vnf_set(size=30)
    sfc_size = 100
    model = Model(topo, generate_sfc_list(topo, vnf_set, sfc_size))
    model.draw_topo(level=1)

    iteration(model)
    Configuration.para = True
    iteration(model)


@print_run_time
def main_dc():
    topo = topology.data_center_example()
    vnf_set = generate_vnf_set(size=30)
    sfc_size = 100
    model = Model(topo, generate_sfc_list2(topo, vnf_set, sfc_size))
    model.draw_topo(1)

    # Configuration.para = False
    # linear_programming(model)
    # rounding_to_integral(model, rounding_method=rounding_one)
    # model.clear()

    Configuration.para = True
    config.DC_CHOOSING_SERVER = True

    linear_programming(model)
    rounding_to_integral(model, rounding_method=rounding_one)


if __name__ == '__main__':
    main_dc()
