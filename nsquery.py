#!/usr/bin/env python

import os
import sys
import json
import time

import numpy as np

# from estimator import Train, Predict
from estimator import TrainNg, Predict
from util.cmd import RED, YELLOW

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('%s <sample_dir> [K]' % sys.argv[0])
        sys.exit(0)

    K = 4
    if len(sys.argv) > 2:
        K = int(sys.argv[2])

    basedir = sys.argv[1]
    querydirs = os.listdir(basedir)

    samples = []
    rho, theta = None, None

    train_out = open('output/train.log', 'w')
    train_time_out = open('output/train-time.log', 'w')
    test_time_out = open('output/test-time.log', 'w')
    train_rho = []

    for query in querydirs:
        filelist = os.listdir(os.path.join(basedir, query))
        trains = [f[:-5] for f in filelist if f.endswith('.json') and f.startswith('train')]
        trains.sort()

        print(YELLOW('='*30 + ' Train ' + '='*30))
        for name in trains:
            print('Reading sample from %s' % name)
            flow_file = name + '.json'
            rate_file = name + '-final.nsout'
            if rate_file in filelist:
                flow_path = os.path.join(basedir, query, flow_file)
                flows = json.load(open(flow_path))

                rate_path = os.path.join(basedir, query, rate_file)
                rates = np.array(open(rate_path).read().split(), dtype=float)

                samples.append({'flows': flows, 'rates': rates})

            print('New sample updated.')
            begin_time = time.time()
            rho, theta, err = TrainNg(samples, K, theta)
            end_time = time.time()
            train_time_out.write('%f\n' % (end_time - begin_time))
            print('Estimated scaling factor: %s' % rho)
            train_out.write('%s\n' % ' '.join([str(x) for x in rho]))
            train_rho.append(rho)

        tests = [f[:-5] for f in filelist if f.endswith('.json') and f.startswith('test')]
        tests.sort()

        test_abs_out = open('output/abs-%s.log' % query, 'w')
        test_rel_out = open('output/rel-%s.log' % query, 'w')
        print(YELLOW('='*30 + ' Predict ' + '='*30))
        for name in tests:
            print('Retrieved query from %s' % name)
            flow_file = name + '.json'
            query_file = 'query' + name[4:] + '.json'
            rate_file = name + '-final.nsout'
            if rate_file in filelist:
                flow_path = os.path.join(basedir, query, flow_file)
                flows = json.load(open(flow_path))

                query_path = os.path.join(basedir, query, query_file)
                query_num = len(json.load(open(query_path)))

                rate_path = os.path.join(basedir, query, rate_file)
                rates = np.array(open(rate_path).read().split(), dtype=float)

                begin_time = time.time()
                rates_esti = Predict(flows, rho, K=4)
                end_time = time.time()
                test_time_out.write('%f\n' % (end_time - begin_time))
                abs_err = rates_esti - rates
                rel_err = abs_err / rates
                abs_err = abs_err[:query_num]
                rel_err = rel_err[:query_num]
                print(RED('Absolute error of prediction: %s' % (abs_err)))
                print(RED('Relative error of prediction: %s' % (rel_err)))
                test_abs_out.write('%s\n' % ' '.join([str(x) for x in abs_err]))
                test_rel_out.write('%s\n' % ' '.join([str(x) for x in rel_err]))

        test_abs_out.close()
        test_rel_out.close()

    train_out.close()
    train_time_out.close()
    test_time_out.close()
