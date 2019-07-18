#!/usr/bin/python3
from para_placement.solution import *


def main():
    print("PLACEMENT MAIN")

    # parameter init
    Configuration.para = True

    model = generate_model(48, 300)
    model.save(file_name="model_data.pkl")
    # model = Model.load(file_name="model_data.pkl")
    model.draw_topo()

    ob1 = greedy(model)
    model.clear()

    optimal = linear_programming(model)
    model.save(file_name="solved_model.pkl")

    ob2 = rounding_to_integral(model, rounding_method=rounding_greedy)

    model = Model.load(file_name="solved_model.pkl")
    ob3 = rounding_to_integral(model, rounding_method=rounding_one)

    print("\n>>>>>>>>>> Result Summary <<<<<<<<<<")
    print(model)
    print()
    print('optimal: {}'.format(optimal))
    print('greedy: {}'.format(ob1))
    print('ILP greedy: {}'.format(ob2))
    print('ILP one+greedy: {}'.format(ob3))


if __name__ == '__main__':
    main()
