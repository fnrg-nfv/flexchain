import sys
import matplotlib.image as mpimg
import matplotlib.pyplot as plt


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 show_eps.py [eps_file_name]")
    else:
        filename = sys.argv[1]
        img = mpimg.imread(filename)
        imgplot = plt.imshow(img)
        plt.show()


if __name__ == "__main__":
    main()
