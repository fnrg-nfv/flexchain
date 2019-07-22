import pickle
import matplotlib.pyplot as plt


def main():
    file_name = 'result2.pkl'
    with open(file_name, 'rb') as _input:
        result = pickle.load(_input)
        _input.close()

    for key in result:
        for key2 in result[key]:
            print(key, key2, result[key][key2][0])

    draw_plot(result)


def draw_plot(result, save_file_name=''):
    x = [key for key in result]
    index = 0
    y_optimal = [result[key]["optimal"][index] for key in result]
    y_greedy = [result[key]["greedy"][index] for key in result]
    y_heuristic1 = [result[key]["ILP greedy"][index] for key in result]
    y_heuristic2 = [result[key]["ILP one"][index] for key in result]

    # 在当前绘图对象中画图（x轴,y轴,给所绘制的曲线的名字，画线颜色，画线宽度）
    plt.plot(x, y_optimal, label="optimal", color="red", linewidth=1)
    plt.plot(x, y_greedy, label="greedy", color="blue", linewidth=1)
    plt.plot(x, y_heuristic1, label="ILP greedy", color="brown", linewidth=1)
    plt.plot(x, y_heuristic2, label="ILP one", color="black", linewidth=1)

    # X轴的文字
    plt.xlabel("Number of SFC Requests")

    # Y轴的文字
    plt.ylabel("Objective Value")

    # 图表的标题
    plt.title("Carnet")

    # Y轴的范围
    # plt.ylim(-1.2, 1.2)

    plt.grid(linestyle='--')  # 显示网格
    plt.legend()  # 显示图示

    if save_file_name:
        plt.savefig('{}.eps'.format(save_file_name), format='eps')

    plt.show()  # 显示图


if __name__ == '__main__':
    main()
