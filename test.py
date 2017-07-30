#!/usr/bin/env python

import os
import sys
import json

import numpy as np

from estimator import Train

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
    names = [f[:-5] for f in filelist if f.endswith('.json')]
    for name in names:
        flow_file = name + '.json'
        rate_file = name + '.mnout'
        if rate_file in filelist:
            flow_path = os.path.join(basedir, flow_file)
            flows = json.load(open(flow_path))
            rate_path = os.path.join(basedir, rate_file)
            rates = np.array(open(rate_path).read().split(),
                             dtype=float)/1e6
            samples.append({'flows': flows, 'rates': rates})

    rho = Train(samples, K)
    print(rho)
