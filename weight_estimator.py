#!/usr/bin/env python

import numpy as np
from scipy.optimize import fmin_slsqp

def Utility(A, c, a, w, x):
    """
    A: routing matrix
    c: capacity vector
    alpha: vector of base utility factors
    w: vector of weight factors
    x: equilibrium bandwidth
    """
    A = np.array(A)
    J = len(a)
    K = len(c)
    assert A.shape == (K, J)
    assert len(w) == J
    assert len(x) == J

    L = 0
    for j in range(J):
        if a[j] == 1:
            L += w[j] * np.log(x[j])
        else:
            L += w[j] * np.power(x[j], 1-a[j]) / (1-a[j])

    return L

def Jac(a, w, x):
    J = len(a)
    assert len(w) == J
    assert len(x) == J

    return np.array([w[j] * np.power(x[j], -a[j]) for j in range(J)])

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

def Lagrangian(A, c, a, w, x, _lambda):
    """
    A: routing matrix
    c: capacity vector
    alpha: vector of base utility factors
    w: vector of weight factors
    x: equilibrium bandwidth
    _lambda: Lagrange Multiplier
    """
    K = len(c)
    assert len(_lambda) == K

    L = Utility(A, c, a, w, x)

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

if __name__ == '__main__':
    # A = np.mat([[1, 1, 0, 0, 1], [1, 0, 0, 1, 0], [0, 1, 1, 0, 0]])
    A = np.mat([[0, 0, 1, 1], [1, 0, 0, 1], [0, 1, 1, 0]])
    c = [1, 1, 1]
    a = [1, 1, 1, 1]
    # w = [1, 1, 1, 1]
    # w = [1, 1, 1, 1, 1]
    th = [np.arccos(1/np.sqrt(i)) for i in range(len(a), 1, -1)]
    w = Spherical2Cartesian(th)
    # w = [1., 1.4608004, 1.00000105, 1.46079935, 1.4608004]
    K = len(c)
    J = len(a)
    # The real w should be [2, 1, 1]
    x_real = [0.4, 0.6, 0.4, 0.6]
    # x_real = [0.3, 0.3, 0.3, 0.3, 0.3]
    # x_real = [0.272, 0.350, 0.571, 0.677, 0.342]
    # x_real = [0.384, 0.571, 0.388, 0.567, 0.1]
    x_esti = []
    x_esti.extend(x_real)
    # x_esti.extend([1, 1])
    x_err = 0

    N = 100
    err = 0.01
    step = 0.01 * np.pi

    it = 0
    while True:
        print('Before Iter %d: w=%s, x0=%s' % (it, w, x_esti))

        # Estimate x
        # La = lambda x: -Lagrangian(A, c, a, w, x[:J], x[J:])
        # res = minimize(La, x_esti, method='nelder-mead', options={'xtol': 1e-6, 'disp': True})
        func_util = lambda x: -Utility(A, c, a, w, x)
        func_jac = lambda x: -Jac(a, w, x)
        # cons = Cons(A, c, a)
        # res = minimize(func_util, x_esti, jac=func_jac, constraints=cons,
        #                method='SLSQP', options={'disp': True})
        cons_func = lambda x: ConsFunc(A, c, a, x)
        cons_joc = lambda x: ConsJoc(A, c, a, x)
        x_esti = fmin_slsqp(func_util, x_real, fprime=func_jac,
                         f_ieqcons=cons_func, fprime_ieqcons=cons_joc, disp=1)
        x_err = np.linalg.norm(x_esti - x_real)

        print('After Iter %d: x=%s, err=%f' % (it, x_esti, x_err))
        it += 1
        if x_err <= err or it > N:
            break

        # Compute \nabla x
        D = np.bmat([[np.diag([w[j]*a[j]*np.power(x_esti[j], -a[j]-1) for j in range(J)]), A.T],
                      [A, np.zeros((K, K))]])
        C = np.bmat([[np.diag([np.power(x_esti[j], a[j]) for j in range(J)])], [np.mat(c).T * np.ones((1, J))]])
        DW = D.I * C
        DWX = DW[:J]

        # Update w
        dth = np.array(x_esti * DWX * SphericalJoc(th))[0]
        # th -= step * dth / np.linalg.norm(dth)
        th -= step * dth
        w = Spherical2Cartesian(th)
    print('Final Result: ', w, x_esti)
