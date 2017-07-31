#!/usr/bin/env python

import matplotlib.pyplot as plot
import math
from statistics import mean, stdev

if __name__ == '__main__':
    N = 10
    T = {}
    for i in range(N):
        with open('5x10/time-%d.log' % i, 'r') as f:
            t = list(map(float, f.readlines()))
            print(t)

        for j in range(len(t)):
            T[j] = (T[j] if j in T else []) + [t[j]]

    mt, sd = [], []
    for i in sorted(T.keys()):
        mt += [mean(T[i])]
        sd += [stdev(T[i])]

    fig, ax = plot.subplots()
    x = range(len(T))
    ax.errorbar(x, mt, sd)

    plot.xlabel('Number of Samples', fontsize=14)
    plot.ylabel('Training Time (s)', fontsize=14)

    fig.savefig('time.pdf')
