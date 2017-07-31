#!/usr/bin/env python

import os
import sys
import json

import numpy as np

# from estimator import Train, Predict
from estimator import TrainNg, Predict
from util.cmd import RED, YELLOW

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('%s <sample_dir> [K] [F] [S]' % sys.argv[0])
        sys.exit(0)

    K = 4
    F = 10
    S = 10
    if len(sys.argv) > 2:
        K = int(sys.argv[2])
    if len(sys.argv) > 3:
        F = int(sys.argv[3])
    if len(sys.argv) > 4:
        S = int(sys.argv[4])

    basedir = sys.argv[1]
    filelist = os.listdir(basedir)

    samples = []
    trains = ['test%d-%d-%d' % (K, j, i)
              for j in range(F, 2*F+1)
              for i in range(1, S//2+1)]

    rho, theta = None, None

    train_out = open('output/train.log', 'w')
    train_rho = []
    print(YELLOW('='*30 + ' Train ' + '='*30))
    for name in trains:
        print('Reading sample from %s' % name)
        flow_file = name + '.json'
        rate_file = name + '.mnout'
        if rate_file in filelist:
            flow_path = os.path.join(basedir, flow_file)
            flows = json.load(open(flow_path))
            rate_path = os.path.join(basedir, rate_file)
            rates = np.array(open(rate_path).read().split(), dtype=float)/1e6
            samples.append({'flows': flows, 'rates': rates})

        print('New sample updated.')
        rho, theta, err = TrainNg(samples, K, theta)
        print('Estimated scaling factor: %s' % rho)
        train_out.write('%s\n' % ' '.join([str(x) for x in rho]))
        train_rho.append(rho)

    train_out.close()

    tests = ['test%d-%d-%d' % (K, j, i)
             for j in range(F, 2*F+1)
             for i in range(S//2+1, S+1)]

    for i in range(S//2-1, len(train_rho), S//2):
        test_abs_out = open('output/test-abs-%d.log' % i, 'w')
        test_rel_out = open('output/test-rel-%d.log' % i, 'w')
        print(YELLOW('='*25 + ' Predict: Cycle %d ' % i + '='*25))
        for name in tests[i-4:i+1]:
            flow_file = name + '.json'
            rate_file = name + '.mnout'
            if rate_file in filelist:
                flow_path = os.path.join(basedir, flow_file)
                flows = json.load(open(flow_path))
                rate_path = os.path.join(basedir, rate_file)
                rates = np.array(open(rate_path).read().split(), dtype=float)/1e6
                rates_esti = Predict(flows, rho, K=4)
                abs_err = rates_esti - rates
                rel_err = abs_err / rates
                print(RED('Absolute error of prediction: %s' % (abs_err)))
                print(RED('Relative error of prediction: %s' % (rel_err)))
                test_abs_out.write('%s\n' % ' '.join([str(x) for x in abs_err]))
                test_rel_out.write('%s\n' % ' '.join([str(x) for x in rel_err]))

        test_abs_out.close()
        test_rel_out.close()

