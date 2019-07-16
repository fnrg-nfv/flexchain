#!/usr/bin/python3
from para_placement.solution import *


def main():
    print("Placement Main")

    Configuration.para = True

    model = generate_model(64, 100)
    # model.save(file_name="model_data.pkl")
    # model = Model.load(file_name="model_data.pkl")
    model.draw_topo()

    greedy(model)

    model.clear()

    linear_programming(model)
    model.output_configurations()
    rounding_to_integral(model)
    model.output_accepted_configuration()


if __name__ == '__main__':
    main()
