#!/usr/bin/env python3

import numpy as np
from scipy.optimize import fmin_slsqp

from util.const import TCP_ALPHA

def Utility(A, c, alpha, rho, x, rho_idx=None):
    """
    A: routing matrix
    c: capacity vector
    alpha: vector of base utility factors
    rho: vector of scaling factors
    x: equilibrium bandwidth
    rho_idx: index of scaling factor each flow has
    """
    A = np.array(A)
    J = len(alpha)
    K = len(c)
    rho_idx = rho_idx or range(J)
    assert A.shape == (K, J)
    assert len(rho_idx) == J
    assert set(range(len(rho))).issuperset(rho_idx)
    assert len(x) == J

    L = 0
    for j in range(J):
        if alpha[j] == 1:
            L += rho[rho_idx[j]] * np.log(x[j])
        else:
            L += rho[rho_idx[j]] * np.power(x[j], 1-alpha[j]) / (1-alpha[j])

    return L

def Jac(alpha, rho, x, rho_idx=None):
    J = len(alpha)
    rho_idx = rho_idx or range(J)
    assert len(rho_idx) == J
    assert set(range(len(rho))).issuperset(rho_idx)
    assert len(x) == J

    return np.array([rho[rho_idx[j]] * np.power(x[j], -alpha[j]) for j in range(J)])

def ConsFunc(A, c, x):
    A = np.array(A)
    J = len(x)
    K = len(c)
    assert A.shape == (K, J)

    return np.array([
        x[j] for j in range(J)
    ] + [
        c[k] - np.dot(A[k], x) for k in range(K)
    ])

def ConsJoc(A, c, x):
    A = np.array(A)
    J = len(x)
    K = len(c)
    assert A.shape == (K, J)

    return np.array([
        [1 if i==j else 0 for i in range(J)] for j in range(J)
    ] + [
        -A[k] for k in range(K)
    ])

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

def Estimate(A, c, alpha, p0, x, p0_idx=None,
             iter=100, tol=0.01, step=0.01*np.pi, spherical=True):
    _p0 = p0

    transform = lambda p: Spherical2Cartesian(p) if spherical else p
    p0 = transform(_p0)

    K = len(c) # The number of fully utilized links
    J = len(alpha) # The number of flows
    p0_idx = p0_idx or range(J)

    x_esti = x[:]
    x_err = 0

    it = 0
    while True:
        print('Before Iter %d: p=%s, x0=%s' % (it, p0, x))

        # Estimate x
        func_util = lambda x: -Utility(A, c, alpha, p0, x, p0_idx)
        func_jac = lambda x: -Jac(alpha, p0, x, p0_idx)
        cons_func = lambda x: ConsFunc(A, c, x)
        cons_joc = lambda x: ConsJoc(A, c, x)
        x_esti = fmin_slsqp(func_util, x, fprime=func_jac,
                            f_ieqcons=cons_func, fprime_ieqcons=cons_joc, disp=1)
        x_err = np.linalg.norm(x_esti - x)

        print('After Iter %d: x=%s, err=%f' % (it, x_esti, x_err))
        it += 1
        if x_err <= tol or it > iter:
            break

        # Compute \nabla x
        D = np.bmat([[np.diag([p0[j]*alpha[j]*np.power(x_esti[j], -alpha[j]-1)
                               for j in range(J)]), A.T],
                     [A, np.zeros((K, K))]])
        CX = np.zeros((J, len(p0)))
        for j, i in np.ndindex(CX.shape):
            if p0_idx[j] == i:
                CX[j, i] = np.power(x_esti[j], -alpha[j])
        C = np.bmat([[CX],
                     [np.mat(c).T * np.ones((1, len(p0)))]])
        if np.linalg.det(D) == 0:
            print('Error(-1): matrix D is not invertible. It is possible that matrix A has full 0 row or column.')
            break
        DW = D.I * C
        DWX = DW[:J]

        # Update p0
        if spherical:
            _dp = 2 * np.array((x_esti/x - 1) / x * DWX * SphericalJoc(_p0))[0]
        else:
            _dp = 2 * np.array((x_esti/x - 1) / x * DWX)[0]
        _p0 -= step * _dp
        print('               dp=%s' % _dp)
        p0 = transform(_p0)
    print('Final Result: ', p0, x_esti)
    return _p0, x_esti

def RoutingMatrix(flows):
    links = {}
    F = len(flows)
    for i in range(F):
        f = flows[i]
        slink = tuple(f['from'] + [0])
        if slink not in links.keys():
            links[slink] = np.zeros(F)
        rflows = links[slink]
        rflows[i] = 1
        dlink = tuple(f['to'] + [1])
        if dlink not in links.keys():
            links[dlink] = np.zeros(F)
        rflows = links[dlink]
        rflows[i] = 1

    A = []
    signal = lambda l, lp: (1 in l-lp) + 2*(-1 in l-lp)

    _links = list(links.keys())
    while _links:
        k = _links.pop()
        l = links[k]
        valid = True
        for kp in _links:
            lp = links[kp]
            s = signal(l, lp)
            if s < 2:
                _links.remove(kp)
            elif s == 2:
                valid = False
                break
        if valid:
            A.append(l)

    return np.mat(A)

def RhoIndex(flows, K, method='sender-hc'):
    K2 = K//2
    F = len(flows)
    rho_idx = [0] * F
    tcps = list(TCP_ALPHA.keys())
    T = len(tcps)
    tcp_idx = {tcps[i]:i for i in range(T)}
    for i in range(F):
        f = flows[i]
        si, sj, sk = f['from']
        di, dj, dk = f['to']
        tcp = f['tcp']
        hc = 2 * (si != di) or 1 * (sj != dj) or 0
        if method == 'sender-hc':
            rho_idx[i] = (si * K + sj * K2 + sk) * 3 + hc
        elif method == 'tcp-hc':
            rho_idx[i] = tcp_idx[tcp] * T + hc
    return rho_idx

def Train(samples, K=4):
    """
    samples: A list of samples.
    K: The scale of Clos topology. (default: 4)

    A sample should be the following format:

    {
      "flows": [], // The specification of running flows
      "rates": []  // The equilibrium bandwidth of each flow
    }
    """
    K2 = K//2
    K = K2*2
    RHO = K * K2 * K2 * 3
    # theta = np.pi/2 * np.random.random(RHO)
    theta = [np.arccos(1/np.sqrt(i)) for i in range(RHO, 1, -1)]
    for sample in samples:
        flows = sample['flows']
        x = sample['rates']
        A = RoutingMatrix(flows)
        L, F = A.shape
        c = [1] * L
        alpha = [TCP_ALPHA[flows[i]['tcp']] for i in range(F)]
        rho_idx = RhoIndex(flows, K)

        theta, new_x = Estimate(A, c, alpha, theta, x, p0_idx=rho_idx, step=0.001*np.pi)
    rho = Spherical2Cartesian(theta)
    return rho

def Predict(flows, rho, K=4):
    K2 = K//2
    K = K2*2
    A = RoutingMatrix(flows)
    L, F = A.shape
    c = [1] * L
    alpha = [TCP_ALPHA[flows[i]['tcp']] for i in range(F)]
    rho_idx = RhoIndex(flows, K)
    x0 = np.array([1.]*F) / F

    rho, x = Estimate(A, c, alpha, rho, x0, p0_idx=rho_idx, iter=0, spherical=False)
    return x

if __name__ == '__main__':
    # Training phase
    A = np.mat([[1, 1, 0, 0], [1, 0, 0, 1], [0, 1, 1, 0]])
    c = [1] * A.shape[0]
    a = [1] * A.shape[1]
    # th = [np.arccos(1/np.sqrt(i)) for i in range(len(a), 1, -1)]
    th = np.pi/2 * np.random.random(len(a)-1)
    x_real = [ 0.54880000000000004, 0.45199999999999996, 0.54800000000000004, 0.42960000000000003 ]

    th_esti, x_esti = Estimate(A, c, a, th, x_real, iter=300)
    w_esti = Spherical2Cartesian(th_esti)

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
