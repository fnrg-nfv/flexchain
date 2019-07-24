import pickle
import string
import time


def extract_str(filename) -> string:
    return filename.split('/')[-1].split('.')[0]


def current_time():
    return time.strftime("%m_%d_%H_%M_%S", time.localtime())


def save_obj(obj, filename):
    with open(filename, 'wb') as output:
        pickle.dump(obj, output, pickle.HIGHEST_PROTOCOL)
        output.close()
