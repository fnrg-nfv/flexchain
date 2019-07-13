#!/usr/bin/python3
from para_placement.solution import *


def main():
    print("Placement Main")
    model = generate_model(32, 100)
    print(model)

    classic_ilp(model)

    # generate_route_list(model.topo, model.sfc_list[0])
    # generate_configuration(model.topo, model.sfc_list[0])


if __name__ == '__main__':
    main()
