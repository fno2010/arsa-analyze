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
        self.A = np.array(A)
        self.AT = self.A.T

        self.argmin_g = argmin_g
        self.B = np.eye(self.M)
        self.BT = np.eye(self.M)

        self.c = np.array(c)

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

        e = max(((self.x - xk)/xk)**2)
        self.x, self.z, self.u = xk, zk, uk
        return e

    def dump(self):
        print(sum(self.f(self.x)))
        print("x=", self.x)
        print("z=", self.z)
        print("u=", self.u)

    def solve(self, niter, step=1, debug=False):
        for i in range(niter):
            e = self.iterate()
            if debug:
                if (i+1) % step == 0:
                    self.dump()
                    print(e)
            if e < 1e-4:
                break
        if debug:
            self.dump()
        return self.x, self.z, self.u

class FullADMM(ADMM):

    def __init__(self, f, A, c, rho=1):
        ADMM.__init__(self, f, None, None, A, c, rho)

    def update_x(self, f, rho, A, AT, u, c):
        N = self.N
        xs = np.array(self.x)
        uTA = [np.dot(AT[i], u) for i in range(N)]

        for i in range(N):
            xi = xs[i]

            aa = np.dot(AT[i], AT[i])
            _a = rho * aa
            _b = uTA[i] - rho * (np.dot(AT[i], c) + aa * xi)
            _c = -1
            dx = lambda _x: _a * _x + _b + _c / _x

            xs[i] = max(0, (-_b + np.sqrt(_b**2 - 4 * _a * _c))/(2*_a))

            sq = lambda _x: np.array(AT[i] * (_x - xi) - c)
            pr = lambda _sqx: np.dot(u, _sqx) + rho / 2 * sum(_sqx**2)
            obj = lambda _x: -f(_x) + pr(sq(_x))

            fprime = lambda _x: -1/np.maximum(_x, 1e-4)
            pprime = lambda _x: uTA[i]
            ppprime = lambda _sqx: np.array(np.dot(AT[i], _sqx))
            jac = lambda _x: fprime(_x) + pprime(_x) + rho * ppprime(sq(_x))


            xsi = fmin_slsqp(obj, np.ones(1), fprime=jac,
                             bounds=[(1e-3, np.inf)], disp=0)
            if xs[i] - xsi > 1e-2:
                print("error:", xs[i], xsi)
            c += AT[i] * (xi - xs[i])

        return xs

    def update_z(self, rho, B, BT, u, c):
        M = len(B)
        xs = np.array(self.z)

        uTB = u

        for i in range(M):
            xi = xs[i]
            sq = lambda _x: (_x - xi) - c[i]
            pr = lambda _x: u[i] * _x + rho / 2 * sum(_x**2)
            obj = lambda _x: pr(sq(_x))

            pprime = lambda _x: uTB[i]
            ppprime = lambda _sqx: _sqx
            jac = lambda _x: pprime(_x) + rho * ppprime(sq(_x))

            xs[i] = fmin_slsqp(obj, np.zeros(1), fprime=jac,
                               bounds=[(1e-4, np.inf)], iter=10, disp=0)
            c += (xi - xs[i])
        return xs

    def iterate(self):
        x, z, u = self.x, self.z, self.u
        A, B = self.A, self.B
        AT, BT = self.AT, self.BT
        c = self.c
        rho = self.rho
        N, M = self.N, self.M
        f = self.f

        b = np.array([c[i] - safedot(B[i], z) - safedot(A[i], x) for i in range(M)])
        # iterate x
        for i in range(10):
            xk = self.update_x(f, rho, A, AT, u, b)
            self.x = xk

        # iterate z
        zk = self.update_z(rho, B, BT, u, b)

        # iterate u
        uk = u - rho * b

        e = max(((self.x - xk)/xk)**2)
        self.x, self.z, self.u = xk, zk, uk
        return e

def argmin_f(f, rho, A, AT, u, c):
    M, N = A.shape

    sq = lambda _x: np.array([safedot(A[i], _x) - c[i] for i in range(M)])
    pr = lambda _sqx: np.dot(u, _sqx) + rho / 2 * sum(_sqx**2)
    fs = lambda _x: sum(f(_x))
    obj = lambda _x: -fs(_x) + pr(sq(_x))

    uTA = [np.dot(AT[i], u) for i in range(N)]
    pprime = lambda _x: np.array(uTA)
    ppprime = lambda _sqx: np.array([np.dot(AT[j], _sqx) for j in range(N)])
    fprime = lambda _x: -1/np.maximum(_x, 1e-4) + 1e2 * np.sign(np.minimum(_x - 1e-4, 0))
    jac = lambda _x: fprime(_x) + pprime(_x) + rho * ppprime(sq(_x))

    x = np.ones(N)

    b = np.asarray(A)[0]
    xs = fmin_ncg(obj, x, fprime=jac,
                  disp=0)
                    #bounds=[(0, np.inf) for i in range(N)], disp=0)
    return xs

def argmin_f2(f, rho, A, AT, u, c):
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
    xs = fmin_slsqp(obj, x, fprime=jac,
                    bounds=[(0, np.inf) for i in range(N)], iter=10, disp=0)
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
                    bounds=[(1e-4, np.inf) for i in range(M)], iter=10, disp=0)
    return xs

if __name__ == '__main__':
    import sys, random
    H, F = sys.argv[1:]
    H, F = int(H), int(F)

    hosts = list(range(H))
    pairs = [random.sample(hosts, 2) for i in range(F)]

    A = [[] for i in range(H)]
    for i in range(H):
        A[i] = [1 if pairs[j][0] == i or pairs[j][1] == i else 0 for j in range(F)]

    #A = [[1, 0, 0], [1, 1, 0], [1, 0, 1]]
    #H = 3
    #F = 3
    A = np.array(A)
    c = np.array([1 for i in range(H)])

    f1 = lambda x: np.log(np.maximum(x, 1e-4)) + 1e2 * np.minimum(x - 1e-4, 0)
    f2 = lambda x: np.log(x+1e-4)

    from cvxopt import matrix
    from cvxsolver import acent
    B = matrix(A, tc='d')
    b = matrix(c.flatten(), (H, 1), 'd')
    x1 = acent(B, b, 10)
    x2 = acent(B, b, 100)

    from numsolver import solve
    x, u = solve(A, c, np.ones(F), np.ones(F), 10)

    print(sum(f1(x1)), np.max(A * np.array(x1) - c))
    print(sum(f1(x2)), np.max(A * x2 - c))
    print(sum(f1(x)), np.max(A * x - c))

    admm = ADMM(f1, argmin_f, argmin_g, A, c)
    x, _, _ = admm.solve(5, 5, debug=False)
    print(sum(f1(x)), np.max(A * x - c))
    x, _, _ = admm.solve(200, 200, debug=False)
    print(sum(f1(x)), np.max(A * x - c))

    #admm2 = FullADMM(f2, A, c)
    #x1, z1, u1 = admm2.solve(10, 10)

    #admm3 = FullADMM(f2, A, c)
    #x2, z2, u2 = admm3.solve(50, 50)

    #print("diff:", max(((x1 - x2)/x1)**2))
