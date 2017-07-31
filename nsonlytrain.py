#!/usr/bin/env python

import os
import sys
import json
import time

import numpy as np

from estimator import TrainNg
from util.cmd import YELLOW

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('%s <sample_dir> [K]' % sys.argv[0])
        sys.exit(0)

    K = 4
    if len(sys.argv) > 2:
        K = int(sys.argv[2])

    basedir = sys.argv[1]
    querydirs = os.listdir(basedir)

    for i in range(len(querydirs)):
        samples = []
        rho, theta = None, None
        train_out = open('output/train-%d.log' % i, 'w')
        time_out = open('output/time-%d.log' % i, 'w')

        for query in querydirs[i:] + querydirs[:i]:
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
                print('Estimated scaling factor: %s' % rho)
                train_out.write('%s\n' % ' '.join([str(x) for x in rho]))
                time_out.write('%f\n' % (end_time - begin_time))

        train_out.close()
        time_out.close()
