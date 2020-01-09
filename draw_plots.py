import collections
import os
import pickle
from itertools import cycle
import matplotlib.pyplot as plt
import numpy as np
from scipy.interpolate import make_interp_spline, BSpline

from para_placement.helper import add_recursively, is_int, save_obj, load_file


def main_time():
    result = load_file('./results/time/time.pkl')
    print(result)
    x, data = result
    plt.yscale('log')
    pure_draw_plot(x, data, xlabel='Size of topology',
                   ylabel='time (s)', save_file_name='time')


def main():
    result = load_file('./results/compare/total_01_09_16_20_09')
    print_dict(result)
    for k in result:
        del result[k]['optimal']
    draw_plot(result, save_file_name='')
    draw_plot(result, save_file_name='', index=2, ylabel="Average Latency")


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
    for root, _, files in os.walk(directory):
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


def print_dict(d):
    for k in d:
        print(k, d[k])
    print()


def main_k():
    result = load_file("./results/k/total_01_08_19_46_05")
    result1 = load_file("./results/k/total_01_08_21_08_03")
    result2 = load_file("./results/k/total_01_08_21_12_09")
    result3 = load_file("./results/k/total_01_08_22_56_54")
    result4 = load_file("./results/k/total_01_08_18_30_31")
    result5 = load_file("./results/k/total_01_09_14_26_57")
    print_dict(result)
    print_dict(result1)
    print_dict(result2)
    print_dict(result3)
    print_dict(result4)
    print_dict(result5)
    result = result5

    # del result[4096]
    x = np.array([k for k in result])
    x.sort()

    rorp_y = np.array([result[i]['RORP'][0] for i in x])
    rorp_time_y = np.array([result[i]['RORP time'] for i in x])
    print(x, rorp_y,  rorp_time_y)

    fig, ax1 = plt.subplots()

    color = 'tab:red'
    ax1.set_xlabel("k")
    ax1.set_ylabel("RORP Accepted Requests", color=color)
    ax1.plot(x, rorp_y, color=color)
    ax1.tick_params(axis='y', labelcolor=color)

    ax2 = ax1.twinx()

    color = 'tab:blue'
    ax2.set_ylabel("Time", color=color)
    ax2.plot(x, rorp_time_y, color=color)
    ax2.tick_params(axis='y', labelcolor=color)

    fig.tight_layout()

    # plt.savefig('test.png')
    plt.show()


def draw_plot(result, title='', save_file_name='', index=0, xlabel='Number of SFC Requests', ylabel="Accepted Requests"):
    x = [key for key in result]  # number of sfc requests
    # index = 0  # objective value
    data = {}

    for size in result:
        for legend in result[size]:
            if legend not in data:
                data[legend] = []
            data[legend].append(result[size][legend][index])

    pure_draw_plot(x, data, title, save_file_name,
                   xlabel=xlabel, ylabel=ylabel)


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
    marker_it = iter(['s', '^', 'o'])
    linestyle_it = iter(['-', '--', ':'])
    # cycol = cycle('brcmk')
    # marker_it = iter(['s',  'o'])
    # linestyle_it = iter(['-', ':'])
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
            check = input("Overwrite File?(y/N)")
            if check == "y":
                plt.savefig(save_file_name, format='eps')
        else:
            plt.savefig(save_file_name, format='eps')

    plt.show()  # 显示图


if __name__ == '__main__':
    main()
