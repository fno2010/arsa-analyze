#!/usr/bin/env python

import os
import sys
import json
import numpy as np

if __name__ == '__main__':

    basedir = sys.argv[1]
    querydirs = os.listdir(basedir)

    vegas_abs = []
    vegas_rel = []
    reno_abs = []
    reno_rel = []
    for query in querydirs:
        filelist = os.listdir(os.path.join(basedir, query))
        tests = [f[:-5] for f in filelist if f.endswith('.json') and f.startswith('query')]
        tests.sort()
        test_abs = [np.array(x.split(), dtype=float) for x in open('output/abs-%s.log' % query, 'r').readlines()]
        test_rel = [np.array(x.split(), dtype=float) for x in open('output/rel-%s.log' % query, 'r').readlines()]
        for i in range(len(tests)):
            name = tests[i]
            query_file = name + '.json'
            query_path = os.path.join(basedir, query, query_file)
            queries = json.load(open(query_path))
            for j in range(len(queries)):
                if queries[j]['tcp'] == 'vegas':
                    vegas_abs.append(test_abs[i][j])
                    vegas_rel.append(test_rel[i][j])
                elif queries[j]['tcp'] == 'reno':
                    reno_abs.append(test_abs[i][j])
                    reno_rel.append(test_rel[i][j])

    with open('output/abs-vegas-tcp.log', 'w') as f:
        f.write('%s' % ' '.join([str(x) for x in vegas_abs]))
    with open('output/rel-vegas-tcp.log', 'w') as f:
        f.write('%s' % ' '.join([str(x) for x in vegas_rel]))
    with open('output/abs-reno-tcp.log', 'w') as f:
        f.write('%s' % ' '.join([str(x) for x in reno_abs]))
    with open('output/rel-reno-tcp.log', 'w') as f:
        f.write('%s' % ' '.join([str(x) for x in reno_rel]))
