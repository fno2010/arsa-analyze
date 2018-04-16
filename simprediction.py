#!/usr/bin/env python3

import numpy as np

def simulate(A, c):
    H, F = A.shape

    from numsolver import solve

    start = datetime.datetime.now()
    x, u = solve(A, c, np.ones(F), np.ones(F), 10)
    end = datetime.datetime.now()
    print(end - start)

if __name__ == '__main__':
    import time, datetime
    import sys, random
    H = sys.argv[1]
    Fs = sys.argv[2:]
    H, Fs = int(H), map(int, Fs)

    hosts = list(range(H))

    last = 0
    A = [[] for i in range(H)]
    for cnt in Fs:
        F = cnt - last
        pairs = [random.sample(hosts, 2) for i in range(F)]
        for i in range(H):
            A[i] += [1 if pairs[j][0] == i or pairs[j][1] == i else 0 for j in range(F)]
        last = cnt

        simulate(np.array(A), np.array([1 for i in range(H)]))
