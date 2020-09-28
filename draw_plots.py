#!/usr/bin/python3
import glob
import os
from itertools import cycle

import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np

from para_placement.helper import *

font = {
    'family': 'Times New Roman',
    'weight': 'normal',
    'size': 17,
}

legendfont = {
    'family': 'Times New Roman',
    'weight': 'normal',
    'size': 14,
}


def main_time():
    result = load_and_print(glob.glob("./results/time/total*")[-1])

    x, data = transfer_result(result)

    data['RORP'] = data['RORP time']
    data['heuristic'] = data['greedy time']
    del data['greedy time']
    del data['optimal']
    del data['greedy']
    del data['RORP time']

    print(x, data)
    plt.yscale('log')
    draw_plot(x, data, xlabel='Topology Size', ylabel='Running Time (s)',
              save_file_name='time', colors='rg', linestyles=['--', ':'], markers='^o')


def main_compare():
    filenames = glob.glob("./results/compare/total*")
    filenames.sort()
    result = load_and_print(filenames[-1])

    x, data = transfer_result(result, 0)
    data['FlexChain+PARC'] = data['heuristic']
    data['Parabox+naïve'] = data['PARABOX-naïve']
    data['NFP+naïve'] = data['NFP-naïve']

    print(data)

    draw_plot(x, data, save_file_name='compare_sfc', legends=[
        'Chain w/o parallelism', 'Parabox+naïve', 'NFP+naïve', 'FlexChain+PARC'], colors='ymcr',
              linestyles=[':', ':', ':', '--'], markers='h x^')


def main_compare_latency():
    filenames = glob.glob("./results/compare/total*")
    filenames.sort()
    result = load_and_print(filenames[-1])

    x, data = transfer_result(result, 2)
    data['FlexChain+PARC'] = data['heuristic']
    data['Parabox+naïve'] = data['PARABOX-naïve']
    data['NFP+naïve'] = data['NFP-naïve']

    print(data)

    draw_plot(x, data, ylabel='Average SFC Latency (ms)',
              save_file_name='compare_latency',
              legends=['Chain w/o parallelism',
                       'Parabox+naïve', 'NFP+naïve', 'FlexChain+PARC'],
              colors='ymcr', linestyles=[':', ':', ':', '--'], markers='h x^', y_formatter='%.2f')


def main_compare_resource():
    filenames = glob.glob("./results/compare/total*")
    filenames.sort()
    result = load_and_print(filenames[-1])

    colors = np.array([
        (250, 120,  78),  # red
        (200, 188, 245),  # purple
        (88, 184, 148),  # blue
        (255, 212,  37)   # yellow
    ])/255

    x, data = transfer_result(result, 3)
    data['FlexChain+PARC'] = data['heuristic']
    data['Parabox+naïve'] = data['PARABOX-naïve']
    data['NFP+naïve'] = data['NFP-naïve']

    draw_plot_bar(
        x, data, ylabel='Resource Utilization',
        save_file_name='compare_resource',
        legends=[
            'NFP+naïve',
            'Parabox+naïve',
            'Chain w/o parallelism',
            'FlexChain+PARC'
        ],
        colors=colors, y_formatter='%.2f')


def main_vl2():
    filenames = glob.glob("./results/VL2/total*")
    filenames.sort()
    result = load_and_print(filenames[-2])
    x, data = transfer_result(result, index=0)
    result2 = load_and_print(filenames[-1])
    x2, data2 = transfer_result(result2, index=0)
    data.update(data2)
    add_zero(x, data)
    data['ROR'] = data['RORP']
    data['PARC'] = data['heuristic']
    del data['RORP']
    del data['heuristic']
    print(x, data)
    draw_plot(x, data, legends=['optimal', 'ROR',
                                'PARC'], save_file_name='vl2')


def main_fattree():
    filenames = glob.glob("./results/fattree/total*")
    filenames.sort()
    result = load_and_print(filenames[-1])
    x, data = transfer_result(result, index=0)
    add_zero(x, data)
    data['ROR'] = data['RORP']
    data['PARC'] = data['heuristic']
    del data['RORP']
    del data['heuristic']
    print(x, data)
    draw_plot(x, data, legends=['optimal', 'ROR',
                                'PARC'], save_file_name='fattree')


def main_bcube():
    sizes = [20 * (i + 1) for i in range(10)]
    result = {}
    for size in sizes:
        filenames = glob.glob("./results/Bcube/{}_*".format(size))
        if filenames:
            filenames.sort()
            print(filenames[-1])
            result[size] = load_file(filename=filenames[-1])

    filenames = glob.glob("./results/Bcube/total_01*")
    filenames.sort()
    result2 = load_and_print(filenames[-1])
    result.update(result2)

    x, data = transfer_result(result, index=0)

    op_result = load_and_print(
        glob.glob("./results/Bcube/op_*")[-1])
    x2, data2 = transfer_result(op_result, index=0)

    data.update(data2)

    add_zero(x, data)
    data['ROR'] = data['RORP']
    data['PARC'] = data['heuristic']
    print(x, data)
    draw_plot(x, data, legends=['optimal', 'ROR',
                                'PARC'], save_file_name='bcube')


# what's this???
def main_bcube_grtt():
    filenames = glob.glob("./results/Bcube/total_grp256_*")
    filenames.sort()
    result = load_and_print(filenames[-1])

    x, data = transfer_result(result, index=0)

    op_result = load_and_print(
        glob.glob("./results/Bcube/op_*")[-1])
    x2, data2 = transfer_result(op_result, index=0)

    data.update(data2)

    add_zero(x, data)
    data['ROR'] = data['grp']
    data['PARC'] = data['heuristic']
    print(x, data)
    draw_plot(x, data, legends=['optimal', 'ROR',
                                'PARC'], save_file_name='bcube')


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
    result = load_and_print(filenames[-3])
    result.update(load_and_print(filenames[-2]))
    result.update(load_and_print(filenames[-1]))

    del result[4096]
    del result[1536]
    x = np.array([k for k in result])
    x.sort()

    rorp_y = np.array([result[i]['RORP'][0] for i in x])
    rorp_time_y = np.array([result[i]['RORP time'] for i in x])
    print(x, rorp_y, rorp_time_y)

    fig, ax1 = plt.subplots(figsize=(6.4, 4.8))

    color = 'tab:red'
    k_font = font.copy()
    k_font['style'] = 'italic'
    ax1.set_xlabel("k", k_font)
    ax1.set_ylabel("Number of Accepted Requests", font, color=color)
    ax1.set_ylim(60, 100)
    l1 = ax1.plot(x, rorp_y, color=color, linestyle='--',
                  marker='^', linewidth=2, label='Accepted Requests', ms=8)
    ax1.tick_params(axis='y', labelcolor=color)

    ax2 = ax1.twinx()

    color = 'tab:blue'
    ax2.set_ylabel("Running Time (s)", font, color=color)
    l2 = ax2.plot(x, rorp_time_y, color=color, linestyle=':',
                  marker='x', linewidth=1.5, label='Running Time', ms=8)
    ax2.set_ylim(200, 1800)
    ax2.tick_params(axis='y', labelcolor=color)

    ax1.set_xticklabels(ax1.get_xticks(), font)
    ax1.set_yticklabels(ax1.get_yticks(), font)
    ax2.set_yticklabels(ax2.get_yticks(), font)
    ax1.xaxis.set_major_formatter(ticker.FormatStrFormatter('%d'))
    ax1.yaxis.set_major_formatter(ticker.FormatStrFormatter('%d'))
    ax2.yaxis.set_major_formatter(ticker.FormatStrFormatter('%d'))

    lns = l1 + l2
    labs = [l.get_label() for l in lns]
    ax1.legend(lns, labs, loc='lower right', prop=legendfont)

    # fig.tight_layout()
    plt.grid(linestyle='--')

    if input("Save this eps?(y/N)") == 'y':
        plt.savefig('eps/k.eps', format='eps')
    # Note: plt.savefig() must before plt.show()
    plt.show()


def main_parallel_overhead():
    x = [64, 128, 256, 512, 1024, 1500]
    y1 = [206, 214, 367, 398, 559, 755]
    y2 = [184, 194, 286, 302, 376, 441]

    # plt.xticks( range(6), (64, 128, 256, 512, 1024, 1500) )
    plt.grid(linestyle='--')
    draw_plot(x, {'Copy': y1, 'Merge': y2}, save_file_name="parallel_overhead", xlabel='Packet size (bytes)',
              ylabel='Average time overhead(ns)', colors='rg', markers='so',
              linestyles=['-', '-'], x2ticks=False)


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


def add_zero(x, data):
    x.insert(0, 0)
    for legend in data:
        data[legend].insert(0, 0)


def draw_plot(x, data,
              legends=[],
              save_file_name='',
              xlabel='Number of SFC Requests',
              ylabel="Number of Accepted Requests",
              title='',
              colors='brgcmk',
              markers='s^ox',
              linestyles=['-', '--', ':'],
              x2ticks=True,
              x_formatter="%d",
              y_formatter="%d",
              legend_bbox_to_anchor=None,
              show_legend=True,
              figsize=(6.4, 4.8)):
    color_cy = cycle(colors)
    marker_cy = cycle(markers)
    linestyle_cy = cycle(linestyles)
    plt.figure(figsize=figsize)
    if not legends:
        legends = [k for k in data]
    for legend in legends:
        plt.plot(
            x, data[legend], marker=next(marker_cy), label=legend, color=next(color_cy), linewidth=2, ms=8,
            linestyle=next(linestyle_cy)
        )

    if x2ticks:
        plt.xticks(x)

    plt.xlabel(xlabel, font)
    plt.ylabel(ylabel, font)
    plt.title(title)
    if show_legend:
        if legend_bbox_to_anchor:
            plt.legend(bbox_to_anchor=legend_bbox_to_anchor, prop=legendfont)
        else:
            plt.legend(prop=legendfont)

    ax = plt.gca()
    ax.yaxis.grid(True, linestyle='--')
    ax.set_xticklabels(ax.get_xticks(), font)
    ax.set_yticklabels(ax.get_yticks(), font)
    ax.xaxis.set_major_formatter(ticker.FormatStrFormatter(x_formatter))
    ax.yaxis.set_major_formatter(ticker.FormatStrFormatter(y_formatter))

    if save_file_name:
        write = True
        save_file_name = './eps/{}.eps'.format(save_file_name)
        if os.path.exists(save_file_name):
            if input("Overwrite File?(y/N)") != "y":
                write = False
        if write:
            plt.savefig(save_file_name, format='eps', bbox_inches='tight')

    plt.show()

    plt.show()


def draw_plot_bar(
        x, data, legends,
        save_file_name='',
        xlabel='Number of SFC Requests',
        ylabel="Number of Accepted Requests",
        title='',
        colors='brgcmk',
        x2ticks=True,
        x_formatter="%d",
        y_formatter="%d",
        legend_bbox_to_anchor=None):

    color_cy = cycle(colors)
    if not legends:
        legends = [k for k in data]

    pos = np.arange(len(x))  # the label locations
    width = 0.2  # the width of the bars
    bias = width*(len(legends)-1)/2
    basepos = pos-bias

    i = 0
    for legend in legends:
        d = np.array(data[legend])
        plt.bar(basepos + i*width, d * 100, label=legend,
                width=width, color=next(color_cy), alpha=1)
        i += 1

    plt.xlabel(xlabel, font)
    plt.ylabel(ylabel, font)
    plt.title(title)
    if legend_bbox_to_anchor:
        plt.legend(bbox_to_anchor=legend_bbox_to_anchor, prop=legendfont)
    else:
        plt.legend(prop=legendfont)

    ax = plt.gca()
    ax.yaxis.grid(True, linestyle='--')
    ax.set_axisbelow(True)
    ax.set_xticklabels(x, font)
    plt.xticks(pos, x)
    ax.set_yticklabels(ax.get_yticks(), font)
    # ax.xaxis.set_major_formatter(ticker.FormatStrFormatter(x_formatter))
    ax.yaxis.set_major_formatter(ticker.PercentFormatter())
    ax.set_ylim(0, 100)

    if save_file_name:
        write = True
        save_file_name = './eps/{}.eps'.format(save_file_name)
        if os.path.exists(save_file_name):
            if input("Overwrite File?(y/N)") != "y":
                write = False
        if write:
            plt.savefig(save_file_name, format='eps', bbox_inches='tight')

    plt.show()


def main_para_prob():
    filenames = glob.glob("./results/para_prob/*")
    filenames.sort()
    result = load_and_print(filenames[-1])
    x, data = transfer_result(result, index=0)
    data['Base'] = [data['RORP'][0]] * len(data['RORP'])
    data['ROR'] = data['RORP']
    data['PARC'] = data['heuristic']
    del data['RORP']
    del data['heuristic']
    for i in range(len(x)):
        x[i] = round(x[i], 1)
    print(x, data)
    draw_plot(x, data, save_file_name='para_prob', x_formatter="%.1f", xlabel='Parallel Probability between NFs',
              colors='krg', markers=' ^o', linestyles=['-', '--', ':'])


def get_offline_data():
    filenames = glob.glob("./results/VL2/total*")
    filenames.sort()
    result = load_and_print(filenames[-2])
    x, data = transfer_result(result, index=0)
    result2 = load_and_print(filenames[-1])
    x2, data2 = transfer_result(result2, index=0)
    data.update(data2)
    add_zero(x, data)
    data['ROR'] = data['RORP']
    data['PARC'] = data['heuristic']
    del data['optimal']
    del data['RORP']
    del data['heuristic']
    for key in data:
        data[key] = data[key][::2]
    return data


def main_online(alg='PARC'):
    filenames = glob.glob("./results/online/*")
    filenames.sort()
    result = load_and_print(filenames[-1])
    data = {}
    for batch_size in result[alg]:
        data[alg + '-' + str(batch_size)] = result[alg][batch_size]

    x = [i for i in range(0, 201, 40)]
    for key in data:
        new_entry = []
        cur = 0
        x_i = 0
        for size in data[key]:
            if size >= x[x_i]:
                new_entry.append(cur)
                x_i += 1
            cur += data[key][size]
        new_entry.append(cur)
        data[key] = new_entry
    data[alg + '-offline'] = get_offline_data()[alg]
    draw_plot(x, data, save_file_name='online-' + alg, linestyles=[':', ':', ':', '--'], markers='s^x ', colors='bmcr')


if __name__ == '__main__':
    main_online(alg='PARC')
    main_online(alg='ROR')
