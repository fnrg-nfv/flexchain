import collections
import os
import pickle
from itertools import cycle

import matplotlib.pyplot as plt

from para_placement.helper import add_recursively, is_int, save_obj, load_file


def main_compare():
    result = get_multiple('results/compare')
    print(result)

    for size in result:
        for key1 in result[size]:
            result[size][key1] = result[size][key1]['heuristic']

    name_map = {
        'normal': "heuristic",
        'unpara': 'heuristic without parallelism',
        'one': 'heuristic with parallelism but placing on one machine'
    }

    for size in result:
        for key in name_map:
            result[size][name_map[key]] = result[size][key]
            del result[size][key]

    for size in result:
        del result[size]['heuristic without parallelism']

    result.pop(100, None)
    # draw_plot(result, save_file_name='', index=0)
    draw_plot(result, save_file_name='compare_amount', index=1, ylabel='Total mount of accepted flows')
    # draw_plot(result, save_file_name='compare_latency', index=2, ylabel='Average Latency (ms)')


def main_time():
    # result = load_file('./results/vl2/total.pkl', True)
    # result = load_file('./results/compare/compare_result_Bcube_07_29_13_10_24.pkl', True)

    result = load_file('./results/time/time.pkl')
    print(result)
    x, data = result
    plt.yscale('log')
    pure_draw_plot(x, data, xlabel='Size of topology', ylabel='time (s)', save_file_name='time')

    # for size in result:
    #     for key1 in result[size]:
    #         result[size][key1] = result[size][key1]['heuristic']

    # result.pop(100, None)
    # draw_plot(result, save_file_name='')


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
    for root, dirs, files in os.walk(directory):
        for file_ in files:
            filename = os.path.join(root, file_)
            print(filename)
            size = 0
            for string in filename.split('_'):
                if is_int(string):
                    size = int(string)
                    break
            with open(filename, 'rb') as _input:
                results[size] = pickle.load(_input)
                _input.close()
                # item = results[size].pop('ILP one', None)
                # if item:
                #     results[size]['heuristic'] = item

    ordered_results = collections.OrderedDict(sorted(results.items()))

    for key, value in ordered_results.items():
        print(key, value)

    return ordered_results


def draw_plot(result, title='', save_file_name='', index=0, xlabel='Number of SFC Requests', ylabel="Objective Value"):
    x = [key for key in result]  # number of sfc requests
    # index = 0  # objective value
    data = dict()

    for size in result:
        for legend in result[size]:
            if legend not in data:
                data[legend] = []
            data[legend].append(result[size][legend][index])

    pure_draw_plot(x, data, title, save_file_name, xlabel=xlabel, ylabel=ylabel)


def pure_draw_plot(x, data, title='', save_file_name='', xlabel='Number of SFC Requests', ylabel="Objective Value"):
    """

    :param ylabel:
    :param xlabel:
    :param x: 横坐标
    :param data: legend : 纵坐标
    :param title:
    :param save_file_name:
    :return:
    """
    cycol = cycle('bgrcmk')
    marker_it = iter(['x', '', '*'])
    linestyle_it = iter(['dotted', 'solid', 'dashed'])

    for legend in data:
        plt.plot(x, data[legend], marker=next(marker_it), label=legend, color=next(cycol), linewidth=2,
                 linestyle=next(linestyle_it))

    # X轴的文字
    plt.xlabel(xlabel)

    # Y轴的文字
    plt.ylabel(ylabel)

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
    main_time()
