# Numerical and Physical Conventions

## Fock-space truncation

A single-mode cutoff `N` represents basis states `|0>` through `|N-1>`. Every
reported state is therefore a finite-dimensional approximation. Convergence
with cutoff must be checked for highly excited, strongly squeezed, cat, and GKP
states.

## State representations

Public state functions accept or return either:

- a one-dimensional normalized ket; or
- a square, Hermitian, positive-semidefinite density matrix with unit trace.

`iqcore.states.density_matrix()` converts either representation to a normalized
density matrix.

## Quadratures

The convention is

```text
x = (a + a†) / sqrt(2)
p = (a - a†) / (i sqrt(2))
```

so `[x, p] = i` and the vacuum variance of either quadrature is `1/2`.

## Tensor ordering

For subsystem dimensions `(d0, d1, ..., dk)`, NumPy C-order tensor-product
indexing is used. The rightmost subsystem index varies fastest. For two equal
cutoffs,

```text
index(n0, n1) = n0 * cutoff + n1.
```

## Beam splitter

Power transmissivity and mixing angle satisfy

```text
T = cos(theta)^2.
```

For zero relative phase, the implemented mode transformation is equivalent to

```text
a_out = a cos(theta) + b sin(theta)
b_out = b cos(theta) - a sin(theta)
```

under the module's unitary convention.

## Loss

All transmissivities are **power** transmissivities. Coherent amplitudes scale
as `sqrt(T)`, while mean photon numbers scale as `T`.

## Wigner function

The vacuum Wigner function follows

```text
W(x, p) = exp[-(x^2 + p^2)] / pi,
```

with numerical normalization `integral W dx dp = 1` on a sufficiently large
grid.

## Tomography

Sign-free tomography reconstructs a finite-dimensional density matrix from
binned absolute-quadrature statistics. The SDP enforces Hermiticity, unit trace,
and positive semidefiniteness. Reported fidelity is fidelity to the chosen
finite-cutoff target, not to an untruncated infinite-dimensional state.

## Communication metrics

Receiver metrics are attack/model specific and asymptotic unless explicitly
stated otherwise. BER and acceptance results should not be interpreted as a
composable quantum-security proof.
