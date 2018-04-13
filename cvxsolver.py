from cvxopt import solvers, matrix, spdiag, log

def acent(A, b, niter):
    m, n = A.size
    def F(x=None, z=None):
        if x is None: return 0, matrix(1.0, (n,1))
        if min(x) <= 0.0: return None
        print(x)
        f = -sum(log(x))
        Df = -(x**-1).T
        if z is None: return f, Df
        print("H.size=", (z[0] * x**-2).size)
        H = spdiag(z[0] * x**-2)
        return f, Df, H
    return solvers.cp(F, G=A, h=b, maxiters=niter, show_progress=False)['x']
