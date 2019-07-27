import datetime
import pickle
import string
import time
from itertools import tee


def extract_str(filename) -> string:
    return filename.split('/')[-1].split('.')[0]


def current_time():
    return time.strftime("%m_%d_%H_%M_%S", time.localtime())


def save_obj(obj, filename):
    with open(filename, 'wb') as output:
        pickle.dump(obj, output, pickle.HIGHEST_PROTOCOL)
        output.close()


# Decorator for running time computing
def print_run_time(func):
    def wrapper(*args, **kw):
        local_time = time.time()
        ret = func(*args, **kw)
        print('[%s] run time: %s' % (func.__name__, datetime.timedelta(seconds=time.time() - local_time)))
        return ret

    return wrapper


def pairwise(iterable):
    """s -> (s0,s1), (s1,s2), (s2, s3), ..."""
    a, b = tee(iterable)
    next(b, None)
    return zip(a, b)


def add_recursively(t1, t2):
    if t1 is None:
        return t2
    if t2 is None:
        return t1

    if type(t1) is not type(t2):
        return None

    if type(t1) is dict:
        ret = dict()
        for key in t1:
            ret[key] = add_recursively(t1[key], t2[key])
        return ret

    if type(t1) is tuple:
        length = min(len(t1), len(t2))
        ret = []
        for i in range(length):
            ret.append(add_recursively(t1[i], t2[i]))
        return tuple(ret)

    if type(t1) is list:
        length = min(len(t1), len(t2))
        ret = []
        for i in range(length):
            ret.append(add_recursively(t1[i], t2[i]))
        return ret

    return t1 + t2
