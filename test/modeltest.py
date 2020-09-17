import unittest
import numpy

from para_placement.model import *


class MyTestCase(unittest.TestCase):
    def test_vnf_para_prob(self):
        size = 30
        for prob in numpy.arange(.1, .9, .1):
            vnf_set = generate_vnf_set_with_para_prob(size, prob)

            pairs = 0
            para_num = 0
            for i in range(size):
                for j in range(i, size):
                    pairs += 1
                    if vnf_set[i].can_run_in_parallel(vnf_set[j]) >= 0:
                        para_num += 1
            self.assertEqual(int(prob * pairs), para_num)

    def test_vnf_para_prob_update(self):
        size = 50
        vnf_set = generate_vnf_set_with_para_prob(size, 0)
        prob = 0
        for i in range(5):
            prob += .2
            update_vnf_set_with_para_prob(vnf_set, .2)

            pairs = 0
            para_num = 0
            for i in range(size):
                for j in range(i, size):
                    pairs += 1
                    if vnf_set[i].can_run_in_parallel(vnf_set[j]) >= 0:
                        para_num += 1
            self.assertEqual(int(prob * pairs), para_num)


if __name__ == '__main__':
    unittest.main()
