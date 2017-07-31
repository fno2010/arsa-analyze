#!/usr/bin/env python

import os
import sys
import json

import numpy as np

# from estimator import Train, Predict
from estimator import TrainNg, Predict
from util.cmd import GREEN, RED, YELLOW

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('%s <sample_dir> [K]' % sys.argv[0])
        sys.exit(0)

    K = 4
    if len(sys.argv) > 2:
        K = int(sys.argv[2])

    basedir = sys.argv[1]
    filelist = os.listdir(basedir)

    samples = []
    trains = [f[:-5] for f in filelist if f.endswith('.json') and f.startswith('train')]
    trains.sort()
    rho, theta = None, None

    train_out = open('output/train.log', 'w')
    train_rho = []
    print(YELLOW('='*30 + ' Train ' + '='*30))
    for name in trains:
        print('Reading sample from %s' % name)
        flow_file = name + '.json'
        rate_file = name + '.nsout'
        # rate_file = name + '-final.nsout'
        if rate_file in filelist:
            flow_path = os.path.join(basedir, flow_file)
            flows = json.load(open(flow_path))
            rate_path = os.path.join(basedir, rate_file)
            rates = np.array(open(rate_path).read().split(), dtype=float)
            samples.append({'flows': flows, 'rates': rates})

        print('New sample updated.')
        # input(GREEN('Continue to train it? (Y/n)'))
        # rho, theta = Train(samples, K, theta)
        rho, theta, err = TrainNg(samples, K, theta)
        print('Estimated scaling factor: %s' % rho)
        train_out.write('%s\n' % ' '.join([str(x) for x in rho]))
        train_rho.append(rho)

    train_out.close()

    tests = [f[:-5] for f in filelist if f.endswith('.json') and f.startswith('test')]
    tests.sort()

    # rho = [0.14433757,  0.14433757,  0.14433757,  0.14433757,  0.14433757,  0.14433757,
    #        0.14433757,  0.14433757,  0.14433757,  0.14433757,  0.14433757,  0.14433757,
    #        0.14433757,  0.14433757,  0.14433757,  0.14433757,  0.14433757,  0.14433757,
    #        0.14433757,  0.14433757,  0.14433757,  0.14433757,  0.14433757,  0.14433757,
    #        0.14433757,  0.14433757,  0.14433757,  0.14433757,  0.14433757,  0.14433757,
    #        0.14433757,  0.14433757,  0.14433757,  0.14433757,  0.14433757,  0.14433757,
    #        0.14433757,  0.14433757,  0.14433757,  0.14433757,  0.14433757,  0.14433757,
    #        0.14433757,  0.14433757,  0.14433757,  0.14433757,  0.14433757,  0.14433757]

    for i in range(len(train_rho)):
        test_abs_out = open('output/test-abs-%d.log' % i, 'w')
        test_rel_out = open('output/test-rel-%d.log' % i, 'w')
        print(YELLOW('='*25 + ' Predict: Cycle %d ' % i + '='*25))
        for name in tests:
            # print('Retrieved query from %s' % name)
            # input(GREEN('Continue to predict it? (Y/n)'))
            flow_file = name + '.json'
            rate_file = name + '.nsout'
            # rate_file = name + '-final.nsout'
            if rate_file in filelist:
                flow_path = os.path.join(basedir, flow_file)
                flows = json.load(open(flow_path))
                rate_path = os.path.join(basedir, rate_file)
                rates = np.array(open(rate_path).read().split(), dtype=float)
                rates_esti = Predict(flows, rho, K=4)
                abs_err = rates_esti - rates
                rel_err = abs_err / rates
                print(RED('Absolute error of prediction: %s' % (abs_err)))
                print(RED('Relative error of prediction: %s' % (rel_err)))
                # output.write('%s\n' % (rates))
                # output.write('%s\n' % (rates_esti))
                test_abs_out.write('%s\n' % ' '.join([str(x) for x in abs_err]))
                test_rel_out.write('%s\n' % ' '.join([str(x) for x in rel_err]))

        test_abs_out.close()
        test_rel_out.close()

