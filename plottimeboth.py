#!/usr/bin/env python

import matplotlib.pyplot as plot
import math
from statistics import mean, stdev

def extract_time_err(dirname, N=10):
    T = {}
    for i in range(N):
        with open(dirname + '/time-%d.log' % i, 'r') as f:
            t = list(map(float, f.readlines()))
            print(t)

        for j in range(len(t)):
            T[j] = (T[j] if j in T else []) + [t[j]]

    mt, sd = [], []
    for i in sorted(T.keys()):
        mt += [mean(T[i])]
        sd += [stdev(T[i])]
    return mt, sd

if __name__ == '__main__':
    mt1, sd1 = extract_time_err('./output.onlytrain5x10', 5)
    mt2, sd2 = extract_time_err('../../data/prophet/ns2-query-5x10-training-only')

    fig, ax = plot.subplots()
    x = range(max(len(mt1), len(mt2)))
    # ax.errorbar(x, mt1, sd1, lolims=True)
    # ax.errorbar(x, mt2, sd2, lolims=True)
    # ax.boxplot(tt)
    ax.plot(x, mt1, label='w/o custom gradient')
    ax.plot(x, mt2, label='custom gradient')

    plot.yscale('log')
    plot.xlabel('Number of Samples', fontsize=14)
    plot.ylabel('Training Time (s)', fontsize=14)
    plot.legend()

    fig.savefig('timeboth.pdf')
