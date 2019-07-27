import pickle
from itertools import cycle

import matplotlib.pyplot as plt

from para_placement.helper import add_recursively


def main():
    filename = 'result_Bcube_07_27_20_10_53.pkl'
    with open(filename, 'rb') as _input:
        result = pickle.load(_input)
        _input.close()
    print(result)

    new_result = dict()
    for key in result:
        item_sum = None
        length = len(result[key])
        for item in result[key]:
            item_sum = add_recursively(item_sum, item)
        item_average = dict()
        for key2 in item_sum:
            ret = []
            for i in range(len(item_sum)):
                ret.append(item_sum[key2][i] / length)
            item_average[key2] = tuple(ret)
        print(key, item_average)
        new_result[key] = item_sum

    draw_plot(new_result, title='', save_file_name="b_cube")


def draw_plot(result, title='Line Plot Demo', save_file_name=''):
    x = [key for key in result]  # number of sfc requests
    index = 0  # objective value

    data = {}

    for size in result:
        for legend in result[size]:
            if legend not in data:
                data[legend] = []
            data[legend].append(result[size][legend][index])

    cycol = cycle('bgrcmk')
    marker_it = iter(['x', '', '*'])
    linestyle_it = iter(['dotted', 'solid', 'dashed'])

    for legend in data:
        plt.plot(x, data[legend], marker=next(marker_it), label=legend, color=next(cycol), linewidth=2,
                 linestyle=next(linestyle_it))

    # X轴的文字
    plt.xlabel("Number of SFC Requests")

    # Y轴的文字
    plt.ylabel("Objective Value")

    # 图表的标题
    plt.title(title)

    # Y轴的范围
    # plt.ylim(-1.2, 1.2)

    plt.grid(linestyle='--')  # 显示网格
    plt.legend()  # 显示图示

    if save_file_name:
        plt.savefig('{}.eps'.format(save_file_name), format='eps')

    plt.show()  # 显示图


if __name__ == '__main__':
    main()
