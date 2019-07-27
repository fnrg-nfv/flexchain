import pickle
from itertools import cycle

import matplotlib.pyplot as plt


def main():
    filename = 'result_Bcube_07_27_13_00_47.pkl'
    with open(filename, 'rb') as _input:
        result = pickle.load(_input)
        _input.close()

    for key in result:
        for key2 in result[key]:
            print(key, key2, result[key][key2][0])

    draw_plot(result, title='Bcube')


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

    for legend in data:
        plt.plot(x, data[legend], label=legend, color=next(cycol), linewidth=1)

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
