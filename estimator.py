#!/usr/bin/env python3

import numpy as np
from scipy.optimize import fmin_slsqp, least_squares

from util.const import TCP_ALPHA
from util.cmd import RED

def Utility(A, c, alpha, rho, _x, rho_idx=None):
    """
    A: routing matrix
    c: capacity vector
    alpha: vector of base utility factors
    rho: vector of scaling factors
    _x: extended variables, x//lambda//slack
        x: equilibrium bandwidth
        lambda: dual variable
        slack: slack variable
    rho_idx: index of scaling factor each flow has
    """
    A = np.array(A)
    J = len(alpha)
    K = len(c)
    rho_idx = rho_idx or range(J)
    assert A.shape == (K, J)
    assert len(rho_idx) == J
    assert set(range(len(rho))).issuperset(rho_idx)
    assert len(_x) == J + 2 * K

    x = _x[:J]
    la = _x[J:J+K]
    s = _x[J+K:]

    # _x = x//lamb//s
    # L(_x) = f(x) - lamb.T * (g(x) - s^2)
    # f(x) = sum(-U(x_i))
    # g(x) = c - A x
    L = 0
    for j in range(J):
        if alpha[j] == 1:
            L += rho[rho_idx[j]] * np.log(x[j])
        else:
            L += rho[rho_idx[j]] * np.power(x[j], 1-alpha[j]) / (alpha[j]-1)

    for k in range(K):
        L -= la[k] * (c[k] - np.dot(A[k], x) - s[k]**2)

    return L

def Jac(A, c, alpha, rho, _x, rho_idx=None):
    A = np.array(A)
    J = len(alpha)
    K = len(c)
    rho_idx = rho_idx or range(J)
    assert A.shape == (K, J)
    assert len(rho_idx) == J
    assert set(range(len(rho))).issuperset(rho_idx)
    assert len(_x) == J + 2 * K

    x = _x[:J]
    la = _x[J:J+K]
    s = _x[J+K:]

    # nabla_x L = nabla_x f - lamb.T * A
    # nalba_lamb = s^2 - g(x)
    # nalba_s = 2 * lamb * s
    return np.array([
        rho[rho_idx[j]] * np.power(x[j], -alpha[j]) - np.dot(la, np.array(A)[:,j]) for j in range(J)
    ] + [
        s[k]**2 - c[k] + np.dot(A[k], x) for k in range(K)
    ] + [
        2 * la[k] for k in range(K)
    ])

def PenaltyFunc(A, c, x):
    A = np.array(A)
    return [np.dot(A[k], x) - c[k] for k in range(len(c))]

def ConsFunc(A, c, x, s):
    A = np.array(A)
    J = len(x)
    K = len(c)
    assert A.shape == (K, J)
    assert len(s) == K

    # c - A x - s^2 = 0
    return np.array([
        c[k] - np.dot(A[k], x) - s[k]**2 for k in range(K)
    ])

def ConsJac(A, c, x, s):
    A = np.array(A)
    J = len(x)
    K = len(c)
    assert A.shape == (K, J)
    assert len(s) == K

    return np.array([
        (-A[k]).tolist() +
        [0 for la in range(K)] +
        [-2*s[i] if i == k else 0 for i in range(K)]
        for k in range(K)
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

def SphericalJac(theta):
    N = len(theta)
    jac = np.zeros((N+1, N))
    sin_t = np.sin(theta)
    cos_t = np.cos(theta)

    for i in range(N+1):
        for j in range(N):
            if j < i:
                jac[i, j] = np.prod([cos_t[t] if t==j else sin_t[t]
                                     for t in range(i-1)]) * cos_t[j]
            elif j == i:
                jac[i, j] = -np.prod(sin_t[:i])
            else:
                jac[i, j] = 0

    return jac

def EstimateX(A, c, alpha, p0, x, p0_idx=None, spherical=True):
    """
    x: the initial x0
    """
    _p0 = p0
    transform = lambda p: Spherical2Cartesian(p) if spherical else p
    p0 = transform(_p0)

    J = len(x)
    K = len(c)
    # TODO: iterate lambda and slack
    _x = np.concatenate((x, np.zeros(2*K)))
    # _x = x//lamb//s
    # L(_x) = f(x) - lamb.T * (g(x) - s^2)
    # f(x) = sum(-U(x_i))
    # g(x) = c - A x
    func_util = lambda _x: -Utility(A, c, alpha, p0, _x, p0_idx)
    func_jac = lambda _x: -Jac(A, c, alpha, p0, _x, p0_idx)
    cons_func = lambda _x: ConsFunc(A, c, _x[:J], _x[J+K:])
    cons_jac = lambda _x: ConsJac(A, c, _x[:J], _x[J+K:])
    icons_func = lambda _x: _x
    icons_jac = lambda _x: np.eye(len(_x))
    _x_esti = fmin_slsqp(func_util, _x, fprime=func_jac,
                         f_eqcons=cons_func, fprime_eqcons=cons_jac,
                         f_ieqcons=icons_func, fprime_ieqcons=icons_jac, disp=0)
    return _x_esti[:J], _x_esti[J:J+K]

def ErrorFunc(A, c, alpha, p0, x, p0_idx=None, spherical=True):
    x_esti, la_esti = EstimateX(A, c, alpha, p0, x, p0_idx, spherical)
    # abs_err = x_esti - x
    # rel_err = abs_err / x
    # print(RED('absolute err=%s' % (abs_err)))
    # print(RED('relative err=%s' % (rel_err)))
    x_err = np.linalg.norm((x_esti - x)/x)**2
    return x_err

def ErrorJac(A, c, alpha, p0, x, p0_idx=None, spherical=True):
    _p0 = p0
    transform = lambda p: Spherical2Cartesian(p) if spherical else p
    p0 = transform(_p0)
    P = len(p0)

    K = len(c)
    J = len(alpha)
    p0_idx = p0_idx or range(J)
    x_esti, la_esti = EstimateX(A, c, alpha, p0, x, p0_idx, spherical=False)

    # FIXME: update error jacobian matrix
    La = np.diag([p0[p0_idx[j]]*alpha[j]*np.power(x_esti[j], -alpha[j]-1)
                  for j in range(J)])
    D = np.bmat([[La, A.T],
                 [np.diag(la_esti)*A, np.diag(PenaltyFunc(A, c, x_esti))]])
    CX = np.zeros((J, P))
    for j, i in np.ndindex(CX.shape):
        if p0_idx[j] == i:
            CX[j, i] = np.power(x_esti[j], -alpha[j])

    C = np.bmat([[CX],
                 [np.zeros((K, P))]])
    if np.linalg.det(D) == 0:
        # print(RED('Warn(-1): matrix D is not invertible. It is possible that matrix A has a full 0 row or column.'))
        DW, _, _, _ = np.linalg.lstsq(D, C, rcond=None)
    else:
        DW = D.I * C
    DWX = DW[:J]

    # Update p0
    dp = (x_esti/x - 1) / x * DWX
    if spherical:
        dp = dp * SphericalJac(_p0)
    return 2 * np.array(dp)[0]

def Estimate(A, c, alpha, p0, x, p0_idx=None,
             iter=100, tol=0.01, step=0.01*np.pi, spherical=True):
    J = len(alpha) # The number of flows
    p0_idx = p0_idx or range(J)
    p0_bound = ([1e-6]*len(p0), [np.pi/2-1e-6]*len(p0))

    error_func = lambda p: ErrorFunc(A, c, alpha, p, x, p0_idx, spherical)
    error_jac = lambda p: ErrorJac(A, c, alpha, p, x, p0_idx, spherical)
    res = least_squares(error_func, p0, jac=error_jac, bounds=p0_bound)
    p_esti = res.x
    err = res.cost

    # print('Final Result: ', p_esti, err)
    return p_esti, err

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

def Train(samples, K=4, theta=None):
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
    if (type(theta) == np.ndarray and len(theta)) or not theta:
        theta = [np.arccos(1/np.sqrt(i)) for i in range(RHO, 1, -1)]
    for sample in samples:
        flows = sample['flows']
        x = sample['rates']
        A = RoutingMatrix(flows)
        L, F = A.shape
        c = [1] * L
        alpha = [TCP_ALPHA[flows[i]['tcp']] for i in range(F)]
        rho_idx = RhoIndex(flows, K)

        theta, err = Estimate(A, c, alpha, theta, x, p0_idx=rho_idx)
        print(RED('Total relative error = %s' % (err)))
    rho = Spherical2Cartesian(theta)
    return rho, theta

def Predict(flows, rho, K=4):
    K2 = K//2
    K = K2*2
    A = RoutingMatrix(flows)
    L, F = A.shape
    c = [1] * L
    alpha = [TCP_ALPHA[flows[i]['tcp']] for i in range(F)]
    rho_idx = RhoIndex(flows, K)
    x0 = np.array([1.]*F) / F

    x, la = EstimateX(A, c, alpha, rho, x0, p0_idx=rho_idx, spherical=False)
    return x

def ErrorFuncNg(As, cs, alphas, p0, xs, p0_idxs=None, spherical=True):
    x_err = 0
    for i in range(len(As)):
        A = As[i]
        c = cs[i]
        alpha = alphas[i]
        x = xs[i]
        p0_idx = p0_idxs[i]
        x_err += ErrorFunc(A, c, alpha, p0, x, p0_idx, spherical)
    return x_err

def ErrorJacNg(As, cs, alphas, p0, xs, p0_idxs=None, spherical=True):
    dp = np.zeros(len(p0))
    for i in range(len(As)):
        A = As[i]
        c = cs[i]
        alpha = alphas[i]
        x = xs[i]
        p0_idx = p0_idxs[i]
        dp += ErrorJac(A, c, alpha, p0, x, p0_idx, spherical)
    return dp

def EstimateNg(As, cs, alphas, p0, xs, p0_idxs=None,
               iter=100, tol=0.01, step=0.01*np.pi, spherical=True):
    S = len(As)
    p0_idxs = p0_idxs or [None] * S
    p0_bound = ([1e-6]*len(p0), [np.pi/2-1e-6]*len(p0))

    error_func = lambda p: ErrorFuncNg(As, cs, alphas, p, xs, p0_idxs, spherical)
    error_jac = lambda p: ErrorJacNg(As, cs, alphas, p, xs, p0_idxs, spherical)
    res = least_squares(error_func, p0, jac=error_jac, bounds=p0_bound)
    p_esti = res.x
    err = res.cost

    # print('Final Result: ', p_esti, err)
    return p_esti, err

def TrainNg(samples, K=4, theta=None):
    K2 = K//2
    K = K2*2
    RHO = K * K2 * K2 * 3
    # theta = np.pi/2 * np.random.random(RHO)
    if (type(theta) == np.ndarray and len(theta)) or not theta:
        theta = [np.arccos(1/np.sqrt(i)) for i in range(RHO, 1, -1)]
    As = []
    cs = []
    alphas = []
    xs = []
    rho_idxs = []
    for sample in samples:
        flows = sample['flows']
        x = sample['rates']
        A = RoutingMatrix(flows)
        L, F = A.shape
        c = [1] * L
        alpha = [TCP_ALPHA[flows[i]['tcp']] for i in range(F)]
        rho_idx = RhoIndex(flows, K)

        As.append(A)
        cs.append(c)
        alphas.append(alpha)
        xs.append(x)
        rho_idxs.append(rho_idx)

    theta, err = EstimateNg(As, cs, alphas, theta, xs, p0_idxs=rho_idxs, step=0.001*np.pi)
    print(RED('Total relative error = %s' % (err)))
    rho = Spherical2Cartesian(theta)
    return rho, theta, err

if __name__ == '__main__':
    # Training phase
    A = np.mat([[1, 1, 0, 0], [1, 0, 0, 1], [0, 1, 1, 0]])
    c = [1] * A.shape[0]
    a = [1] * A.shape[1]
    # th = [np.arccos(1/np.sqrt(i)) for i in range(len(a), 1, -1)]
    th = np.pi/2 * np.random.random(len(a)-1)
    x_real = [ 0.54880000000000004, 0.45199999999999996, 0.54800000000000004, 0.42960000000000003 ]

    th_esti, err = Estimate(A, c, a, th, x_real)
    w_esti = Spherical2Cartesian(th_esti)

    # Prediction phase
    A = np.mat([[1, 1, 0, 0, 1], [1, 0, 0, 1, 0], [0, 1, 1, 0, 0]])
    c = [1] * A.shape[0]
    a = [1] * A.shape[1]
    w_esti.resize(len(a), refcheck=False)
    w_esti[-1] = w_esti[1]
    x_real = [ 0.352, 0.32400000000000002, 0.47599999999999998, 0.62880000000000003, 0.32400000000000002 ]

    # EstimateX for prediction
    x_esti, la_esti = EstimateX(A, c, a, w_esti, x_real, spherical=False)
    abs_err = x_esti - x_real
    rel_err = abs_err / x_real
    print('Absolute error = %s' % (abs_err))
    print('Related error = %s' % (rel_err))
