#!/usr/bin/env python2

import sys

import numpy as np

from random import randint

from mininet.log import setLogLevel
from estimator import Spherical2Cartesian, Estimate
from testcase import ClosTopologyTest
from util.arsaconf import parse_argument
from util.case import Case

class ModifiedClosTopologyTest(ClosTopologyTest):
    def __init__(self, K, config, json):
        self.K = K / 2 * 2
        self.config = config
        self.json = json
        self.min_delay = 60

        Case.__init__(self)

    def result(self):
        rate = []
        for i in range(len(self.flows)):
            l = open('%d.log' % i, 'r').readlines()[-4]
            r = float(l.split()[6]) / 1000
            rate.append(r)
        return rate

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

def UpdateFlows(K, flows, rho, x):
    K2 = K / 2
    K = K2 * 2
    sel = randint(0, len(flows)-1)
    new_flow = flows[sel].copy()
    si, sj, sk = new_flow['from']
    di, dj, dk = new_flow['to']

    new_di = randint(0, K-1)
    new_dj = randint(0, K2-1)
    new_dk = randint(0, K2-1)

    if si == di:
        new_di = di
        if sj == dj:
            new_dj = dj

    new_flow['to'] = [new_di, new_dj, new_dk]

    flows.append(new_flow)
    rho = rho.tolist()
    rho.append(rho[sel])
    x.append(1e-2)
    return flows, rho, x

def RoutingMatrix(flows):
    links = {}
    F = len(flows)
    for i in range(F):
        f = flows[i]
        slink = tuple(f['from'] + [0])
        if slink not in links.keys():
            links[slink] = np.zeros(F)
        rflows = links[slink]
        rflows[i] = 1
        dlink = tuple(f['to'] + [1])
        if dlink not in links.keys():
            links[dlink] = np.zeros(F)
        rflows = links[dlink]
        rflows[i] = 1

    A = []
    signal = lambda l, lp: (1 in l-lp) + 2*(-1 in l-lp)

    _links = links.keys()
    while _links:
        k = _links.pop()
        l = links[k]
        valid = True
        for kp in _links:
            lp = links[kp]
            s = signal(l, lp)
            if s < 2:
                _links.remove(kp)
            elif s == 2:
                valid = False
                break
        if valid:
            A.append(l)

    return np.mat(A)

if __name__ == '__main__':
    setLogLevel('info')
    cmdline = parse_argument()
    config = cmdline.parse_args(sys.argv[1:])

    if config.verbose:
        setLogLevel('debug')

    log_file = open('result.log', 'w')

    F = 10
    K = 4
    log_file.write('Start %d flows in Clos topology (K=%d):\n' % (F, K))

    flows = RandomFlows(F, K)
    log_file.write('Flows:\n')
    log_file.write('%s\n' % flows)

    log_file.write('Testing...\n')
    test = ModifiedClosTopologyTest(K, config, flows)
    log_file.write('Done!\n')

    x = test.result()
    log_file.write('Equilibrium rates: %s\n' % x)

    log_file.write('Setup the training environment...\n')
    A = RoutingMatrix(flows)
    log_file.write('Routing Matrix:\n%s\n' % A)
    c = [1] * A.shape[0]
    log_file.write('Capacity Vector: %s\n' % c)
    a = [1] * A.shape[1]
    log_file.write('Utility Factors: %s\n' % a)
    theta = [np.arccos(1/np.sqrt(i)) for i in range(len(a), 1, -1)]
    log_file.write('Initial Spherical Scaling Factors: %s\n' % theta)
    rho = Spherical2Cartesian(theta)
    log_file.write('Initial Scaling Factors: %s\n' % rho)

    log_file.write('Training the scaling factors...\n')
    new_rho, new_x = Estimate(A, c, a, theta, x)

    log_file.write('The estimated scaling factor: %s\n' % new_rho)
    log_file.write('The estimated error on flow rates: %s\n' % ((new_x - x)/x))

    log_file.write('Updating running flows...\n')
    flows, new_rho, x = UpdateFlows(K, flows, new_rho, x)
    log_file.write('Flows:\n')
    log_file.write('%s\n' % flows)

    log_file.write('Setup the prediction environment...\n')
    A = RoutingMatrix(flows)
    log_file.write('Routing Matrix:\n%s\n' % A)
    c = [1] * A.shape[0]
    log_file.write('Capacity Vector: %s\n' % c)
    a = [1] * A.shape[1]
    log_file.write('Utility Factors: %s\n' % a)
    log_file.write('Estimated Scaling Factors: %s\n' % new_rho)

    log_file.write('Predicting the equilibrium flow rates...\n')
    new_rho, new_x = Estimate(A, c, a, new_rho, x, iter=0, spherical=False)
    log_file.write('The estimated equilibrium flow rates: %s\n' % new_x)

    log_file.write('Validating the prediction...\n')
    log_file.write('Testing...\n')
    new_test = ModifiedClosTopologyTest(K, config, flows)
    log_file.write('Done!\n')

    x = new_test.result()
    log_file.write('The real equilibrium rates: %s\n' % x)

    log_file.write('The estimated error on flow rates: %s\n' % ((new_x - x)/x))

    log_file.close()
