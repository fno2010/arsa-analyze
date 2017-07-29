#!/usr/bin/env python2

import sys

from random import randint

from mininet.log import setLogLevel
from simulation import parse_argument
from testcase import ClosTopologyTest
from util.case import Case

class ModifiedClosTopologyTest(ClosTopologyTest):
    def __init__(self, K, config, json):
        self.K = K / 2 * 2
        self.config = config
        self.json = json
        self.min_delay = 60

        Case.__init__(self)

    def setup_network(self):
        Case.setup_network(self)

def RandomFlows(F, K):
    K2 = K / 2
    K = K2 * 2
    flows = []
    for i in range(F):
        si, sj, sk = randint(0, K-1), randint(0, K2-1), randint(0, K2-1)
        while True:
            di, dj, dk = randint(0, K-1), randint(0, K2-1), randint(0, K2-1)
            if (di, dj, dk) != (si, sj, sk):
                break
        flows.append({"tcp": "vegas", "from": [si, sj, sk], "to": [di, dj, dk]})
    return flows

if __name__ == '__main__':
    setLogLevel('info')
    cmdline = parse_argument()
    config = cmdline.parse_args(sys.argv[1:])

    if config.verbose:
        setLogLevel('debug')

    F = 10
    K = 4
    flows = RandomFlows(F, K)
    ModifiedClosTopologyTest(K, config, flows)
