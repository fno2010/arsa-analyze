#!/usr/bin/env python3

import numpy as np
from scipy.optimize import fmin_slsqp, fmin_ncg, least_squares

def safedot(A, x):
    return np.dot(A, x)

class ADMM(object):
    """
    Alternating direction multiplier method

    Solving:
    f(x) + g(z), where g(z) = 0
    Ax + Bz = c, where B = I

    f: a multi-dimension function, should return an array of results
    argmin_f: the method to optimize x, see argmin_f() below for signature
    argmin_g: the method to optimize z, see argmin_g() below for signature
    A: the constraint matrix
    c: the constraint
    rho: something like a step size
    """

    def __init__(self, f, argmin_f, argmin_g, A, c, rho=1):
        self.M, self.N = A.shape
        assert self.M == len(c)

        self.f = f

        self.argmin_f = argmin_f
        self.A = A
        self.AT = A.T

        self.argmin_g = argmin_g
        self.B = np.eye(self.M)
        self.BT = np.eye(self.M)

        self.c = c

        self.x = np.zeros(self.N)
        self.z = np.zeros(self.M)
        self.u = np.zeros(self.M)

        self.rho = rho

    def iterate(self):
        x, z, u = self.x, self.z, self.u
        A, B = self.A, self.B
        AT, BT = self.AT, self.BT
        c = self.c
        rho = self.rho
        N, M = self.N, self.M
        f = self.f

        # iterate x
        v = [c[i] - safedot(B[i], z) for i in range(M)]
        xk = self.argmin_f(f, rho, A, AT, u, np.array(v))

        # iterate z
        w = [c[i] - safedot(A[i], xk) for i in range(M)]
        zk = self.argmin_g(rho, B, BT, u, np.array(w))

        # iterate u
        delta = [c[i] - np.dot(B[i], zk) - np.dot(A[i], xk) for i in range(M)]
        uk = u - rho * np.array(delta)

        self.x, self.z, self.u = xk, zk, uk

    def solve(self, niter, step=1):
        for i in range(niter):
            self.iterate()
            if i % step == 0:
                print("x=", self.x)
                print("z=", self.z)
                print("u=", self.u)
        return self.x, self.z, self.u

def argmin_f(f, rho, A, AT, u, c):
    M, N = A.shape

    sq = lambda _x: np.array([safedot(A[i], _x) - c[i] for i in range(M)])
    pr = lambda _sqx: np.dot(u, _sqx) + rho / 2 * sum(_sqx**2)
    fs = lambda _x: sum(f(_x))
    obj = lambda _x: -fs(_x) + pr(sq(_x))

    uTA = [np.dot(AT[i], u) for i in range(N)]
    pprime = lambda _x: np.array(uTA)
    ppprime = lambda _sqx: np.array([np.dot(AT[j], _sqx) for j in range(N)])
    fprime = lambda _x: -1/_x
    jac = lambda _x: fprime(_x) + pprime(_x) + rho * ppprime(sq(_x))

    x = np.ones(N)

    b = np.asarray(A)[0]
    xs = fmin_ncg(obj, x, fprime=jac, disp=0)
    return xs

def argmin_g(rho, B, BT, u, c):
    M = len(B)

    sq = lambda _x: _x - c
    pr = lambda _x: np.dot(u, _x) + rho / 2 * sum(_x**2)
    obj = lambda _x: pr(sq(_x))

    uTB = u
    pprime = lambda _x: np.array(uTB)
    ppprime = lambda _sqx: _sqx
    jac = lambda _x: pprime(_x) + rho * ppprime(sq(_x))

    x = np.zeros(M)

    xs = fmin_slsqp(obj, x, fprime=jac,
                    bounds=[(0, np.inf) for i in range(M)], disp=0)
    return xs

if __name__ == '__main__':
    A = np.array([[1, 0, 0], [1, 1, 0], [1, 0, 1]])
    c = np.array([1, 1, 1])

    print(c)

    admm = ADMM(lambda x: np.log(x), argmin_f, argmin_g, A, c)
    admm.solve(10)
