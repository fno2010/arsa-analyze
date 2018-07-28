#!/usr/bin/env python

import matplotlib.pyplot as plot
import numpy as np
from statistics import mean, stdev

if __name__ == '__main__':
    N = 10
    T = {}
    t = []
    for i in range(N):
        with open('test-time-%d.log' % i, 'r') as f:
            t0 = list(map(float, f.readlines()))
            t += t0

        for j in range(len(t0)):
            T[j] = (T[j] if j in T else []) + [t0[j]]

    mt, sd = [], []
    for i in sorted(T.keys()):
        mt += [mean(T[i])]
        sd += [stdev(T[i])]

    fig, ax = plot.subplots()
    ax.errorbar(list(range(len(T))), mt, sd)

    plot.xlabel('Samples', fontsize=14)
    plot.ylabel('Prediction Time (s)')

    fig.savefig('pred-time.pdf')

    t = sorted(t)
    x = range(len(t))
    c = np.cumsum([1.0 / len(t)] * len(t))

    print(t)
    fig, ax = plot.subplots()
    ax.plot(t, c)

    plot.xlabel('Prediction Time (s)', fontsize=14)
    plot.ylabel('CDF')

    fig.savefig('pred-time-cdf.pdf')
