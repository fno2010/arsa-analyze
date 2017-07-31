#!/usr/bin/env python

import matplotlib.pyplot as plot
import math
from statistics import mean, stdev

def dim(vec):
    vec = list(vec)
    return math.sqrt(sum(map(lambda x: x **2, vec))/len(vec))

if __name__ == '__main__':
    rho = {}
    diff = lambda x,y: map(lambda p: p[0] - p[1], zip(x, y))
    for i in range(10):
        with open('5x10/train-%d.log' % i, 'r') as f:
            d = map(lambda l: l.split(' '), f.readlines())
            d = list(map(lambda x: list(map(float, x)), d))
            N = len(d)
            dx = [dim(diff(d[N-1], d[i-1]))/dim(d[N-1]) for i in range(1, N)]
        for j in range(len(dx)):
            rho[j] = (rho[j] if j in rho else []) + [dx[j]]
    mt, sd = [], []
    for i in sorted(rho.keys()):
        mt += [mean(rho[i])]
        sd += [stdev(rho[i])]

    x = range(len(rho))
    fig, ax = plot.subplots()
    ax.errorbar(x, mt, sd)

    plot.xlabel('Number of Samples', fontsize=16)
    plot.ylabel('Relative Error', fontsize=16)

    plot.savefig('diff-rho.pdf')
