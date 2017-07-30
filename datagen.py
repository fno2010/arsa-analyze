#!/usr/bin/env python2.7

import random
import json, sys
from util.arsaconf import parse_argument
from ns2gen import ns2file, generate_ns2, execute_ns2
from closgen import generate_flows

TRAIN_CONF_FP = '%strain-%d.json'
TRAIN_MATRIX_FP = '%strain-%d.matrix'
TEST_CONF_FP = '%stest-%d.json'
TEST_MATRIX_FP = '%stest-%d.matrix'

def generate_training_flows(N, K, tr, prefix):
    N = random.randint(int(N/2), N)
    flows = []
    for i in range(tr):
        conf_file = TRAIN_CONF_FP % (prefix, i)
        matrix_file = TRAIN_MATRIX_FP % (prefix, i)
        flows += [generate_flows(N, K, conf_file, matrix_file)]

    return flows

def generate_predict_flows(L, te, flows, prefix):
    L = random.randint(int(L/2), L)
    all_flows = reduce(lambda x,y: x + y, flows)
    flows = []
    for i in range(te):
        print('training %s' % i)
        tflows = random.sample(all_flows, L)
        conf_file = '%stest-%d.json' % (prefix, i)
        with open(conf_file, 'w') as f:
            json.dump(tflows, f)
        flows += [tflows]

    return flows

def run_flows(K, prefix, target, flows, config):
    for i in range(len(flows)):
        print('testing %s' % i)
        flow = flows[i]
        trace_file = '%s%s-%d.trace' % (prefix, target, i)
        thpt_file = '%s%s-%d.nsout' % (prefix, target, i)
        with open(ns2file, 'w') as f:
            generate_ns2(K, flow, config, trace_file, f)
        execute_ns2(trace_file, thpt_file)

if __name__ == '__main__':
    N, K, prefix, tr, te = sys.argv[1:6]
    N, K, tr, te = int(N), int(K), int(tr), int(te)
    cmd = parse_argument()

    config = cmd.parse_args(sys.argv[6:])

    tr_flows = generate_training_flows(N, K, tr, prefix)
    run_flows(K, prefix, 'train', tr_flows, config)
    te_flows = generate_predict_flows(N, te, tr_flows, prefix)
    run_flows(K, prefix, 'test', te_flows, config)
