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
        print('[%s] run time: %fs' % (func.__name__, time.time() - local_time))
        return ret

    return wrapper


def pairwise(iterable):
    """s -> (s0,s1), (s1,s2), (s2, s3), ..."""
    a, b = tee(iterable)
    next(b, None)
    return zip(a, b)
