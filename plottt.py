#!/usr/bin/env python

import matplotlib.pyplot as plot
import numpy as np
import math
from statistics import mean, stdev

if __name__ == '__main__':
    N = 10
    T = {}
    with open('test-time.log', 'r') as f:
        t0 = list(map(float, f.readlines()))
        t = sorted(t0)

    x = range(len(t))
    c = np.cumsum([1.0 / len(t)] * len(t))

    fig, ax = plot.subplots()
    ax.plot(list(range(len(t0))), t0)

    plot.xlabel('Samples', fontsize=14)
    plot.ylabel('Prediction Time (s)')

    fig.savefig('pred-time.pdf')

    fig, ax = plot.subplots()
    ax.plot(t, c)

    plot.xlabel('Prediction Time (s)', fontsize=14)
    plot.ylabel('CDF')

    fig.savefig('pred-time-cdf.pdf')
