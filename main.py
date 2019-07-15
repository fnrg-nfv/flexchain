#!/usr/bin/python3
from para_placement.solution import *


def main():
    print("Placement Main")
    # model = generate_model(32, 100)
    # model.save(file_name="model_data.pkl")
    # model = Model.load(file_name="model_data.pkl")

    # classic_lp(model)

    # model.save(file_name="solved_model.pkl")
    model = Model.load(file_name="solved_model.pkl")

    print(model)
    model.draw_topo()

    lp_to_ilp(model)


if __name__ == '__main__':
    main()
