import collections
import os
import pickle
from itertools import cycle

import matplotlib.pyplot as plt

from para_placement.helper import add_recursively


def main():
    # result = load_file('./results/vl2/total.pkl', True)
    # result = load_file('./results/bcube/result_Bcube_07_27_20_10_53.pkl', True)

    result = get_multiple('./results/fattree')
    # print(result)

    # new_result = average_duplicated(result)
    # print(new_result)
    # result.pop(100, None)
    # draw_plot(result, save_file_name='vl2_2')


def load_file(filename, p=False):
    with open(filename, 'rb') as _input:
        result = pickle.load(_input)
        _input.close()

    if p:
        for k, v in result.items():
            print(k, v)

    return result


def average_duplicated(result):
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
        new_result[key] = item_average
    return new_result


def get_multiple(directory):
    results = dict()
    # directory = './results/vl2'
    for root, dirs, files in os.walk(directory):
        for file_ in files:
            filename = os.path.join(root, file_)
            print(filename)
            size = int(filename.split('_')[2])
            with open(filename, 'rb') as _input:
                results[size] = pickle.load(_input)
                _input.close()
                item = results[size].pop('ILP one', None)
                if item:
                    results[size]['heuristic'] = item

    ordered_results = collections.OrderedDict(sorted(results.items()))

    for key, value in ordered_results.items():
        print(key, value)

    return ordered_results

    # filename = './results/vl2/total.pkl'
    # with open(filename, 'wb') as output:
    #     pickle.dump(ordered_results, output, pickle.HIGHEST_PROTOCOL)
    #     output.close()


def draw_plot(result, title='', save_file_name=''):
    x = [key for key in result]  # number of sfc requests
    index = 0  # objective value
    data = dict()

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
        save_file_name = './eps/{}.eps'.format(save_file_name)
        if os.path.exists(save_file_name):
            check = input("Overwrite File?")
            if check == "True":
                plt.savefig(save_file_name, format='eps')
        else:
            plt.savefig(save_file_name, format='eps')

    plt.show()  # 显示图


if __name__ == '__main__':
    main()
