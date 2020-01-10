import collections
import os
import glob
import pickle
from itertools import cycle
import matplotlib.pyplot as plt
import numpy as np
from scipy.interpolate import make_interp_spline, BSpline

from para_placement.helper import *


def main_time():
    result = load_and_print(glob.glob("./results/time/total*")[-1])

    x, data = transfer_result(result)

    data['heuristic time'] = data['greedy time']
    del data['greedy time']

    print(data)
    plt.yscale('log')
    pure_draw_plot(x, data, xlabel='Topology Size',
                   ylabel='Time (s)', save_file_name='time')


def main_compare():
    filenames = glob.glob("./results/compare/total*")
    filenames.sort()
    result = load_and_print(filenames[-1])

    x, data = transfer_result(result, 0)
    del data['optimal']
    data['NFP-naive'] = data['OM']
    del data['OM']
    data['Chain w/o parallelism'] = data['NP']
    del data['NP']

    pure_draw_plot(x, data, save_file_name='compare-sfcnum')


def main_compare_latency():
    filenames = glob.glob("./results/compare/large*")
    filenames.sort()
    result = load_and_print(filenames[-1])

    x, data = transfer_result(result, 2)
    del data['optimal']
    data['NFP-naive'] = data['OM']
    del data['OM']
    data['Chain w/o parallelism'] = data['NP']
    del data['NP']

    pure_draw_plot(x, data, ylabel='Time (s)')


def main():
    filenames = glob.glob("./results/Bcube/01*")
    filenames.sort()
    result = load_and_print(filenames[-1])
    draw_plot(result, save_file_name='')


def load_and_print(filename):
    print(filename)
    d = load_file(filename)
    print_dict(d)
    return d


def print_dict(d):
    for k in d:
        print(k, d[k])
    print()


def main_k():
    filenames = glob.glob("./results/k/total_*")
    filenames.sort()
    result = load_and_print(filenames[-2])
    result.update(load_and_print(filenames[-1]))

    del result[4096]
    del result[1536]
    x = np.array([k for k in result])
    x.sort()

    rorp_y = np.array([result[i]['RORP'][0] for i in x])
    rorp_time_y = np.array([result[i]['RORP time'] for i in x])
    print(x, rorp_y,  rorp_time_y)

    fig, ax1 = plt.subplots()

    color = 'tab:red'
    ax1.set_xlabel("k")
    ax1.set_ylabel("Number of Accepted Requests", color=color)
    ax1.set_ylim(62, 100)
    ax1.plot(x, rorp_y, color=color, marker='o')
    ax1.tick_params(axis='y', labelcolor=color)

    ax2 = ax1.twinx()

    color = 'tab:blue'
    ax2.set_ylabel("Time (s)", color=color)
    ax2.plot(x, rorp_time_y, color=color, linestyle=':', marker='s')
    ax2.tick_params(axis='y', labelcolor=color)

    fig.tight_layout()

    plt.show()


def transfer_result(result, index=-1):
    x = [key for key in result]  # number of sfc requests
    x.sort()
    legends = [l for l in result[x[0]]]

    data = {}
    if index >= 0:
        data = {legend: [result[size][legend][index]
                         for size in x] for legend in legends}
    else:
        data = {legend: [result[size][legend]
                         for size in x] for legend in legends}

    return x, data


def draw_plot(result, title='', save_file_name='', index=0, xlabel='Number of SFC Requests', ylabel="Accepted Requests", add_zero=False):
    x, data = transfer_result(result, index)

    # add zero
    if add_zero:
        x.insert(0, 0)
        for legend in data:
            data[legend].insert(0, 0)

    pure_draw_plot(x, data, title, save_file_name,
                   xlabel=xlabel, ylabel=ylabel)


def pure_draw_plot(x, data, title='', save_file_name='', xlabel='Number of SFC Requests', ylabel="Accepted Requests"):
    cycol = cycle('bgrcmk')
    marker_it = iter(['s', '^', 'o', 'x'])
    linestyle_it = iter(['-', '--', ':', '-'])
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
    # plt.ylim(0, 120)

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
    main_compare_latency()
