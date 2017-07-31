#!/usr/bin/env python

import matplotlib.pyplot as plot
import numpy as np
import math
from statistics import mean, stdev

if __name__ == '__main__':
    N = 10
    T = {}
    with open('test-time.log', 'r') as f:
        t = sorted(list(map(float, f.readlines())))

    fig, ax = plot.subplots()
    x = range(len(t))
    c = np.cumsum([1.0 / len(t)] * len(t))
    ax.plot(t, c)

    plot.xlabel('Prediction Time (s)', fontsize=14)
    plot.ylabel('CDF')

    fig.savefig('test-time.pdf')
