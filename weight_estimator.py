#!/usr/bin/env python

import numpy as np
from scipy.optimize import minimize, fmin_slsqp

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

    return np.array([w[j] * np.power(x[j], a[j]) for j in range(J)])

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


if __name__ == '__main__':
    A = np.mat([[1, 1, 0], [1, 0, 1]])
    c = [1, 1]
    a = [1, 1, 1]
    w = [1, 1, 1]
    K = len(c)
    J = len(a)
    # The real w should be [2, 1, 1]
    x_real = [0.5, 0.5, 0.5]
    x_esti = []
    x_esti.extend(x_real)
    # x_esti.extend([1, 1])
    x_err = 0

    N = 100
    err = 0.01
    step = 0.1

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
        if x_err <= err or it > N:
            break

        # Compute \nabla x
        D = np.bmat([[np.diag([w[j]*a[j]*np.power(x_esti[j], -a[j]-1) for j in range(J)]), A.T],
                      [A, np.zeros((K, K))]])
        C = np.bmat([[np.diag([np.power(x_esti[j], a[j]) for j in range(J)])], [np.mat(c).T * np.ones((1, J))]])
        DW = D.I * C
        DWX = DW[:J]

        # Update w
        dw = np.array(x_esti * DWX)[0]
        w -= step * dw / np.linalg.norm(dw)
        w = w / w[0]
        it += 1
    print('Final Result: ', w, x_esti)
