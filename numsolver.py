#!/usr/bin/env python3

from cvxopt import solvers, matrix, spdiag, log
import numpy as np

def solve(A, c, alpha, rho, niter, debug=False):
    B = matrix(A, tc='d')
    c = matrix(c, tc='d')

    m, n = B.size

    assert n == len(alpha)
    assert n == len(rho)
    assert m == len(c)

    alphas = 1 - alpha

    def f(x):
        y = np.array(x.T).flatten()
        return sum(np.where(alphas==0,
                            rho*np.log(y),
                            rho*np.power(y, alphas) / (alphas + 1e-9)))

    def fprime(x):
        y = np.array(x.T).flatten()
        return rho * np.power(y, -alpha)

    def fpprime(x, z):
        print("x.size=", x.size)
        y = np.array(x.T).flatten()
        return z[0] * rho * -alpha * y**(-alpha-1)

    def F(x=None, z=None):
        if x is None:
            return 0, matrix(1.0, (n, 1))
        if min(x) <= 0.0:
            return None
        fx = matrix(-f(x), (1,1))
        print(fx.size)
        fpx = matrix(-fprime(x), (1, n))
        print(fpx.size)
        if z is None:
            return fx, fpx
        fppx = spdiag(matrix(-fpprime(x,z), (n, 1)))
        return fx, fpx, fppx

    ret = solvers.cp(F, G=B, h=c, maxiters=niter, show_progress=False)
    return ret['x'], ret['zl']
