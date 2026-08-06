"""From-first-principles Fock-space reverse-reconciliation Holevo chi(B:E).

Builds the purified thermal-loss channel entirely from truncated Fock operators
-- coherent signal, two-mode-squeezed-vacuum environment purification,
beam-splitter unitary, and homodyne (position-eigenstate) POVM -- and evaluates

    chi(B:E) = S(rho_E) - \int dy p(y) S(rho_{E|y})

for Gaussian modulation p(alpha), ideal homodyne. Compared against the symplectic
covariance-matrix value, which it must reproduce; the point is that this route
never uses the covariance matrix and so independently checks it.

Convention: quadrature x = a + a^dagger (vacuum variance 1, SNU). Position
eigenstate amplitudes <n|y> = 2^{-1/4} psi_n(y/sqrt2), psi_n the standard
harmonic-oscillator eigenfunctions.
"""
import numpy as np
from numpy.polynomial.hermite import hermval
from scipy.linalg import expm
import math


def ann(N):
    return np.diag(np.sqrt(np.arange(1, N)), 1)


def coherent(alpha, N):
    if abs(alpha) < 1e-14:
        v = np.zeros(N, dtype=complex); v[0] = 1.0; return v
    n = np.arange(N)
    logc = -0.5 * abs(alpha) ** 2 + n * np.log(alpha + 0j) \
        - 0.5 * np.cumsum(np.concatenate(([0.0], np.log(np.arange(1, N)))))
    v = np.exp(logc)
    return v / np.linalg.norm(v)


def tmsv(lam, N):
    """Two-mode squeezed vacuum sum lam^n |n,n>, modes (e0,e2), as N*N vector."""
    n = np.arange(N)
    coeff = np.sqrt(1 - lam ** 2) * lam ** n
    psi = np.zeros((N, N), dtype=complex)
    psi[n, n] = coeff
    psi /= np.linalg.norm(psi)
    return psi.reshape(-1)


def bs_unitary(T, N):
    """U = exp[theta (a^dag b - a b^dag)], transmissivity T = cos^2 theta."""
    a = ann(N)
    theta = math.acos(math.sqrt(T))
    G = np.kron(a.conj().T, a) - np.kron(a, a.conj().T)
    return expm(theta * G)


def homodyne_amp(y, N):
    """<n|y> for x = a + a^dag (vacuum variance 1)."""
    from scipy.special import gammaln
    xs = y / math.sqrt(2.0)
    n = np.arange(N)
    log_norm = -0.25 * np.log(np.pi) - 0.5 * (n * np.log(2.0) + gammaln(n + 1))
    H = np.array([hermval(xs, [0] * k + [1]) for k in n])
    psi_n = np.exp(log_norm) * H * np.exp(-xs ** 2 / 2.0)   # standard HO wavefunction
    return 2.0 ** -0.25 * psi_n                             # rescale for x=a+adag


def vn_entropy(rho):
    w = np.linalg.eigvalsh(rho)
    w = w[w > 1e-12]
    return float(-np.sum(w * np.log2(w)))


def fock_chi_be(T, xi, V_A, N=16, n_alpha=25, n_y=61, y_max=9.0, verbose=False):
    # environment occupation reproducing input-referred excess noise xi:
    # Bob variance V_B = T V + (1-T)(2 nbar_E + 1) = T V + 1 - T + T xi  ->
    nbar_E = T * xi / (2.0 * (1.0 - T))
    lam = math.sqrt(nbar_E / (1.0 + nbar_E)) if nbar_E > 0 else 0.0
    U = bs_unitary(T, N)
    env = tmsv(lam, N).reshape(N, N)               # (e0, e2)

    # alpha grid ~ N(0, V_A/4) per quadrature (Var[x_sig]=V_A)
    s = math.sqrt(V_A / 4.0)
    axis = np.linspace(-4 * s, 4 * s, n_alpha)
    da = axis[1] - axis[0]
    W = np.exp(-(axis[:, None] ** 2 + axis[None, :] ** 2) / (2 * s ** 2))
    W /= W.sum()                                    # normalized modulation weights

    ys = np.linspace(-y_max, y_max, n_y)
    dy = ys[1] - ys[0]
    Hy = np.array([homodyne_amp(y, N) for y in ys])  # (n_y, N)

    # Build the stack of Bob-Eve amplitude matrices Psi_p (B0, E) over the alpha grid.
    aa = (axis[:, None] + 1j * axis[None, :]).reshape(-1)
    w_flat = W.reshape(-1)
    keep = w_flat > 1e-9
    aa, w_flat = aa[keep], w_flat[keep]
    P = aa.shape[0]
    Psi = np.empty((P, N, N * N), dtype=complex)
    for p in range(P):
        st = np.einsum('a,ec->aec', coherent(aa[p], N), env).reshape(N * N, N)
        Psi[p] = (U @ st).reshape(N, N * N)               # (B0, E)

    # rho_E = sum_p w_p Tr_{B0}|psi><psi|
    rho_E = np.einsum('p,pbe,pbf->ef', w_flat, Psi, Psi.conj())
    rho_E /= np.trace(rho_E).real
    S_E = vn_entropy(rho_E)

    # conditional: for each y, E_y(p,:) = <y|psi_p>; rho~_{E|y} = E_y^dag diag(w) E_y
    S_cond = 0.0
    py_sum = 0.0
    for k in range(n_y):
        E_y = np.einsum('b,pbe->pe', Hy[k], Psi)          # (P, E)
        rt = E_y.conj().T @ (w_flat[:, None] * E_y)        # (E, E)
        p = np.trace(rt).real
        if p <= 1e-12:
            continue
        py_sum += p * dy
        S_cond += dy * p * vn_entropy(rt / p)
    S_cond /= py_sum
    py_norm = py_sum
    chi = S_E - S_cond
    if verbose:
        print(f"  nbar_E={nbar_E:.4f} lam={lam:.4f} tr(rho_E)~1 "
              f"p(y)_norm={py_norm:.4f} S_E={S_E:.4f} S_cond={S_cond:.4f}")
    return chi


def _chi_symplectic(T, xi, V_A=4.0):
    import math
    def g(x): return 0.0 if x <= 1e-15 else (x + 1) * math.log2(x + 1) - x * math.log2(x)
    V = V_A + 1; cl = (1 - T) / T + xi
    a = V * V * (1 - 2 * T) + 2 * T + T * T * (V + cl) ** 2; b = T * T * (V * cl + 1) ** 2
    r = math.sqrt(max(0, a * a - 4 * b)); l1 = math.sqrt(max(1, (a + r) / 2)); l2 = math.sqrt(max(1, (a - r) / 2))
    c = (V * math.sqrt(b) + T * (V + cl)) / (T * (V + cl)); d = math.sqrt(b) * V / (T * (V + cl))
    r2 = math.sqrt(max(0, c * c - 4 * d)); l3 = math.sqrt(max(1, (c + r2) / 2)); l4 = math.sqrt(max(1, (c - r2) / 2))
    return g((l1 - 1) / 2) + g((l2 - 1) / 2) - g((l3 - 1) / 2) - g((l4 - 1) / 2)


if __name__ == "__main__":
    print("Table IV: first-principles Fock chi_N(B:E) vs symplectic (ideal homodyne, V_A=4)")
    print(f"{'point':16}{'T':>5}{'xi':>6}{'N':>4}{'Fock':>10}{'sympl':>10}{'rel err':>10}")
    for lbl, T, xi in [("pure loss", 0.5, 0.0), ("moderate Raman", 0.5, 0.05), ("high loss", 0.1, 0.05)]:
        s = _chi_symplectic(T, xi)
        for N in (16, 20):
            c = fock_chi_be(T, xi, 4.0, N=N, n_alpha=27, n_y=71)
            print(f"{lbl:16}{T:>5}{xi:>6}{N:>4}{c:>10.5f}{s:>10.5f}{abs(c-s)/s:>10.2e}")
