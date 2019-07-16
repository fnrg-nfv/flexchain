#!/usr/bin/python3
from para_placement.solution import *


def main():
    print("Placement Main")

    Configuration.para = True

    model = generate_model(32, 200)
    model.save(file_name="model_data.pkl")
    # model = Model.load(file_name="model_data.pkl")

    model.draw_topo()

    classic_lp(model)

    model.save(file_name="para_solved_model.pkl")
    # model = Model.load(file_name="solved_model.pkl")

    lp_to_ilp(model)


def main2():
    a = set() | set()


if __name__ == '__main__':
    main2()
