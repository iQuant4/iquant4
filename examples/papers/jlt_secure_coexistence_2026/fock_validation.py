"""Fock-basis convergence validation for the coexistence Holevo machinery.

Validates the truncated-Fock density-matrix kernel used in Section IV-C against
exact analytic references:

* Pure loss: two equiprobable coherent states |+-alpha> through loss T.  Eve's
  ensemble rho_E = 1/2(|beta><beta| + |-beta><-beta|), beta = sqrt(1-T) alpha,
  has exact eigenvalues lambda_pm = 1/2 (1 +- e^{-2|beta|^2}); its von Neumann
  entropy equals the Holevo chi (each conditional state is pure).
* Thermal environment: a single-mode thermal state of occupation n_bar has exact
  entropy g(n_bar) = (n_bar+1)log2(n_bar+1) - n_bar log2 n_bar.  This is the
  environment entropy that enters the coexistence Holevo bound.

Reports, per cutoff N: tail probability, trace error, minimum eigenvalue,
computed value, exact reference, relative error, runtime, and memory.
"""
import time
import tracemalloc
import numpy as np


def coherent_vector(alpha, N):
    n = np.arange(N)
    logc = (-0.5 * abs(alpha) ** 2 + n * np.log(alpha + 0.0j)
            - 0.5 * np.cumsum(np.concatenate(([0.0], np.log(np.arange(1, N))))))
    return np.exp(logc)


def vn_entropy(rho):
    w = np.linalg.eigvalsh(rho)
    w = w[w > 1e-15]
    return float(-np.sum(w * np.log2(w)))


def g_function(nbar):
    if nbar <= 1e-15:
        return 0.0
    return (nbar + 1.0) * np.log2(nbar + 1.0) - nbar * np.log2(nbar)


def pure_loss_row(alpha, T, N):
    beta = np.sqrt(1.0 - T) * alpha
    tracemalloc.start(); t0 = time.perf_counter()
    vp = coherent_vector(beta, N); vm = coherent_vector(-beta, N)
    vp /= np.linalg.norm(vp); vm /= np.linalg.norm(vm)
    rho = 0.5 * (np.outer(vp, vp.conj()) + np.outer(vm, vm.conj()))
    S = vn_entropy(rho)
    dt = time.perf_counter() - t0
    mem = tracemalloc.get_traced_memory()[1]; tracemalloc.stop()
    ov = np.exp(-2.0 * abs(beta) ** 2)
    lam = np.array([0.5 * (1 + ov), 0.5 * (1 - ov)])
    S_exact = float(-np.sum(lam[lam > 0] * np.log2(lam[lam > 0])))
    tail = 1.0 - np.sum(abs(coherent_vector(beta, N)) ** 2)  # pre-normalization tail
    trace_err = abs(np.trace(rho).real - 1.0)
    min_eig = float(np.linalg.eigvalsh(rho).min())
    rel = abs(S - S_exact) / S_exact if S_exact > 0 else abs(S - S_exact)
    return dict(N=N, tail=tail, trace_err=trace_err, min_eig=min_eig,
                val=S, ref=S_exact, rel=rel, ms=dt * 1e3, kb=mem / 1024)


def thermal_row(nbar, N):
    tracemalloc.start(); t0 = time.perf_counter()
    n = np.arange(N)
    p = (nbar ** n) / ((1.0 + nbar) ** (n + 1))
    tail = float(1.0 - p.sum())
    p = p / p.sum()
    rho = np.diag(p).astype(complex)
    S = vn_entropy(rho)
    dt = time.perf_counter() - t0
    mem = tracemalloc.get_traced_memory()[1]; tracemalloc.stop()
    S_exact = g_function(nbar)
    trace_err = abs(np.trace(rho).real - 1.0)
    min_eig = float(np.linalg.eigvalsh(rho).min())
    rel = abs(S - S_exact) / S_exact if S_exact > 0 else abs(S - S_exact)
    return dict(N=N, tail=tail, trace_err=trace_err, min_eig=min_eig,
                val=S, ref=S_exact, rel=rel, ms=dt * 1e3, kb=mem / 1024)


def show(title, rows):
    print(f"\n{title}")
    print(f"{'N':>4}{'tail':>11}{'trace_err':>11}{'min_eig':>11}"
          f"{'value':>10}{'ref':>10}{'rel_err':>10}{'ms':>8}{'KB':>8}")
    for r in rows:
        print(f"{r['N']:>4}{r['tail']:>11.2e}{r['trace_err']:>11.2e}"
              f"{r['min_eig']:>11.2e}{r['val']:>10.5f}{r['ref']:>10.5f}"
              f"{r['rel']:>10.2e}{r['ms']:>8.2f}{r['kb']:>8.1f}")


# Pure-loss (80 km, T=0.025): weak, moderate signals.
show("Pure loss, two coherent states, alpha=1.0, T=0.0251",
    [pure_loss_row(1.0, 0.0251, N) for N in (20, 30, 40)])
show("Pure loss, two coherent states, alpha=2.0, T=0.0251",
    [pure_loss_row(2.0, 0.0251, N) for N in (20, 30, 40)])
# Thermal environment: moderate Raman and a near-security-boundary occupation.
show("Thermal environment, n_bar=0.05 (moderate Raman)",
    [thermal_row(0.05, N) for N in (20, 30, 40)])
show("Thermal environment, n_bar=0.30 (near security boundary)",
    [thermal_row(0.30, N) for N in (20, 30, 40)])
