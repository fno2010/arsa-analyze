#!/usr/bin/env python3

import numpy as np
from scipy.optimize import fmin_slsqp

def Utility(A, c, a, p, x):
    """
    A: routing matrix
    c: capacity vector
    alpha: vector of base utility factors
    p: vector of scaling factors
    x: equilibrium bandwidth
    """
    A = np.array(A)
    J = len(a)
    K = len(c)
    assert A.shape == (K, J)
    assert len(p) == J
    assert len(x) == J

    L = 0
    for j in range(J):
        if a[j] == 1:
            L += p[j] * np.log(x[j])
        else:
            L += p[j] * np.power(x[j], 1-a[j]) / (1-a[j])

    return L

def Jac(a, p, x):
    J = len(a)
    assert len(p) == J
    assert len(x) == J

    return np.array([p[j] * np.power(x[j], -a[j]) for j in range(J)])

def Cons(A, c, a):
    A = np.array(A)
    J = len(a)
    K = len(c)
    assert A.shape == (K, J)

    cons = []
    for j in range(J):
        cons.append({'type': 'ineq',
                     'fun': lambda x: np.array([x[j] - 1e-6]),
                     'jac': lambda x: np.array([1 if i==j else 0
                                                for i in range(J)])})

    for k in range(K):
        cons.append({'type': 'ineq',
                     'fun': lambda x: np.array([c[k] - np.dot(A[k], x)]),
                     'jac': lambda x: -A[k]})

    return tuple(cons)

def ConsFunc(A, c, a, x):
    A = np.array(A)
    J = len(a)
    K = len(c)
    assert A.shape == (K, J)
    assert len(x) == J

    return np.array([
        x[j] for j in range(J)
    ] + [
        c[k] - np.dot(A[k], x) for k in range(K)
    ])

def ConsJoc(A, c, a, x):
    A = np.array(A)
    J = len(a)
    K = len(c)
    assert A.shape == (K, J)
    assert len(x) == J

    return np.array([
        [1 if i==j else 0 for i in range(J)] for j in range(J)
    ] + [
        -A[k] for k in range(K)
    ])

def Lagrangian(A, c, a, p, x, _lambda):
    """
    A: routing matrix
    c: capacity vector
    alpha: vector of base utility factors
    p: vector of scaling factors
    x: equilibrium bandwidth
    _lambda: Lagrange Multiplier
    """
    K = len(c)
    assert len(_lambda) == K

    L = Utility(A, c, a, p, x)

    for k in range(K):
        L -= _lambda[k] * (np.dot(A[k], x) - c[k])
    return L

def Spherical2Cartesian(theta):
    N = len(theta)
    car = np.zeros(N+1)
    sin_t = np.sin(theta)
    cos_t = np.cos(theta)

    car[0] = 1
    for i in range(1, N+1):
        car[i] = car[i-1]*sin_t[i-1]

    for i in range(N):
        car[i] *= cos_t[i]

    return car

def SphericalJoc(theta):
    N = len(theta)
    joc = np.zeros((N+1, N))
    sin_t = np.sin(theta)
    cos_t = np.cos(theta)

    for i in range(N+1):
        for j in range(N):
            if j < i:
                joc[i, j] = np.prod([cos_t[t] if t==j else sin_t[t]
                                     for t in range(i-1)]) * cos_t[j]
            elif j == i:
                joc[i, j] = -np.prod(sin_t[:i])
            else:
                joc[i, j] = 0

    return joc

def Estimate(A, c, a, p0, x, iter=100, tol=0.01, step=0.01*np.pi, spherical=True):
    _p0 = p0

    transform = lambda p: Spherical2Cartesian(p) if spherical else p
    p0 = transform(_p0)

    K = len(c) # The number of fully utilized links
    J = len(a) # The number of flows

    x_esti = x[:]
    x_err = 0

    it = 0
    while True:
        print('Before Iter %d: p=%s, x0=%s' % (it, p0, x_esti))

        # Estimate x
        func_util = lambda x: -Utility(A, c, a, p0, x)
        func_jac = lambda x: -Jac(a, p0, x)
        cons_func = lambda x: ConsFunc(A, c, a, x)
        cons_joc = lambda x: ConsJoc(A, c, a, x)
        x_esti = fmin_slsqp(func_util, x, fprime=func_jac,
                            f_ieqcons=cons_func, fprime_ieqcons=cons_joc, disp=1)
        x_err = np.linalg.norm(x_esti - x)

        print('After Iter %d: x=%s, err=%f' % (it, x_esti, x_err))
        it += 1
        if x_err <= tol or it > iter:
            break

        # Compute \nabla x
        D = np.bmat([[np.diag([p0[j]*a[j]*np.power(x_esti[j], -a[j]-1)
                               for j in range(J)]), A.T],
                     [A, np.zeros((K, K))]])
        C = np.bmat([[np.diag([np.power(x_esti[j], a[j]) for j in range(J)])],
                     [np.mat(c).T * np.ones((1, J))]])
        if np.linalg.det(D) == 0:
            print('Error(-1): matrix D is not invertible. It is possible that matrix A has full 0 row or column.')
            break
        DW = D.I * C
        DWX = DW[:J]

        # Update w
        if spherical:
            _dp = 2 * np.array((x_esti - x) * DWX * SphericalJoc(_p0))[0]
        else:
            _dp = 2 * np.array((x_esti - x) * DWX)[0]
        _p0 -= step * _dp
        print('               dp=%s' % _dp)
        p0 = transform(_p0)
    print('Final Result: ', p0, x_esti)
    return p0, x_esti

if __name__ == '__main__':
    # Training phase
    A = np.mat([[1, 1, 0, 0], [1, 0, 0, 1], [0, 1, 1, 0]])
    c = [1] * A.shape[0]
    a = [1] * A.shape[1]
    th = [np.arccos(1/np.sqrt(i)) for i in range(len(a), 1, -1)]
    w = Spherical2Cartesian(th)
    x_real = [ 0.54880000000000004, 0.45199999999999996, 0.54800000000000004, 0.42960000000000003 ]

    w_esti, x_esti = Estimate(A, c, a, th, x_real, iter=300)

    # Prediction phase
    A = np.mat([[1, 1, 0, 0, 1], [1, 0, 0, 1, 0], [0, 1, 1, 0, 0]])
    c = [1] * A.shape[0]
    a = [1] * A.shape[1]
    w_esti.resize(len(a), refcheck=False)
    w_esti[-1] = w_esti[1]
    x_real = [ 0.352, 0.32400000000000002, 0.47599999999999998, 0.62880000000000003, 0.32400000000000002 ]

    # Iter=0 for prediction
    w_esti, x_esti = Estimate(A, c, a, w_esti, x_real, iter=0, spherical=False)
    abs_err = x_esti - x_real
    rel_err = abs_err / x_real
    print('Absolute error = %s' % (abs_err))
    print('Related error = %s' % (rel_err))
