#!/usr/bin/python3
from para_placement.solution import *
import uuid

topo_files = ['./gml_data/Cernet.gml', './gml_data/Geant2012.gml', './gml_data/Internetmci.gml']


def main():
    print("PLACEMENT MAIN")

    # parameter init
    Configuration.para = True

    # model init
    topo = topology.parse_gml(topo_files[1])
    vnf_set = generate_vnf_set(size=50)
    model = Model(topo, [])

    model.draw_topo(level=1)

    iter_times = 8
    unit = 25
    result = {}

    for i in range(iter_times):
        model.sfc_list.extend(generate_sfc_list(topo=topo, vnf_set=vnf_set, size=unit, base_idx=i * unit))
        model.clear()
        size = unit * i + unit
        result[size] = iteration(model)

    file_name = "result_Geant2012.pkl"
    with open(file_name, 'wb') as output:
        pickle.dump(result, output, pickle.HIGHEST_PROTOCOL)
        output.close()


def iteration(model):
    ob1 = greedy(model)
    model.clear()
    optimal = linear_programming(model)
    file_name = "solved_model_{}.pkl".format(uuid.uuid4())
    model.save(file_name)
    ob2 = rounding_to_integral(model, rounding_method=rounding_greedy)
    model = Model.load(file_name)
    ob3 = rounding_to_integral(model, rounding_method=rounding_one)
    os.remove(file_name)

    print("\n>>>>>>>>>> Result Summary <<<<<<<<<<")
    print(model)
    print()
    print('optimal: {}'.format(optimal))
    print('greedy: {}'.format(ob1))
    print('ILP greedy: {}'.format(ob2))
    print('ILP one+greedy: {}'.format(ob3))
    return {
        "optimal": optimal,
        "greedy": ob1,
        "ILP greedy": ob2,
        "ILP one": ob3
    }


def main2():
    file_name = topo_files[0]

    # model init
    topo = topology.parse_gml(file_name)
    vnf_set = generate_vnf_set(size=30)
    result = {}

    # for size in range(25, 201, 25):
    size = 200
    model = Model(topo, generate_sfc_list(topo, vnf_set, size))
    model.draw_topo()
    iteration(model)
    result[size] = iteration(model)

    file_name = "result_Geant2012.pkl".format(uuid.uuid4())
    with open(file_name, 'wb') as output:
        pickle.dump(result, output, pickle.HIGHEST_PROTOCOL)
        output.close()

    print(result)


if __name__ == '__main__':
    main()
