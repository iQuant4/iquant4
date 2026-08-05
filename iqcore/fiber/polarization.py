"""Polarization effects: PMD and PDL, for the classical and quantum branches.

Real single-mode fiber carries two polarization modes, and small random
birefringence along the fiber couples them.  Two consequences matter for a
coherent long-haul link *and* for polarization-encoded QKD:

* **Polarization-mode dispersion (PMD).**  The two principal states travel at
  slightly different group velocities; the *differential group delay* (DGD)
  between them spreads a pulse and, because the birefringence is random and
  temperature-dependent, the instantaneous DGD is a random variable.  Over a
  fiber of length ``L`` the mean DGD grows as ``D_PMD * sqrt(L)`` (the
  random-walk law), and the instantaneous DGD follows a **Maxwellian
  distribution** — the statistical hallmark this module reproduces and validates.
* **Polarization-dependent loss (PDL).**  Components attenuate one polarization
  more than the other, tilting the received constellation and, combined with
  PMD, causing outages.

The emulator is the textbook **concatenation of birefringent sections**: each
section is a random SU(2) mode-coupling followed by a fixed-DGD retarder, so the
total Jones matrix ``T(ω)`` is frequency-dependent and its DGD — measured here by
**Jones-Matrix Eigenanalysis (JME)** — is Maxwellian with the target mean.  The
same ``T(ω)`` applied to a two-component field reproduces PMD pulse-splitting.

Quantum tie-in: PMD depolarizes a broadband signal, so a polarization-encoded
BB84 qubit picks up a misalignment QBER — :func:`polarization_qber` — that this
module feeds to the QKD branch.  One physical effect, both branches.

References: Gordon & Kogelnik, PNAS 97, 4541 (2000) (PMD fundamentals);
Heffner, IEEE PTL 4, 1066 (1992) (JME DGD measurement).
"""

from __future__ import annotations

from dataclasses import dataclass
from math import pi, sqrt

import numpy as np

from .propagation import TimeGrid

__all__ = [
    "mean_dgd_ps",
    "maxwellian_pdf",
    "sample_dgd_maxwellian",
    "random_su2",
    "PMDFiber",
    "pdl_jones",
    "apply_jones",
    "polarization_qber",
]


def mean_dgd_ps(pmd_param_ps_per_sqrt_km: float, length_km: float) -> float:
    """Mean DGD (ps) of a fiber: ``D_PMD * sqrt(L)`` (random-walk law)."""
    if length_km < 0:
        raise ValueError("length_km must be non-negative")
    return pmd_param_ps_per_sqrt_km * sqrt(length_km)


def maxwellian_pdf(tau_ps: np.ndarray, mean_dgd_ps: float) -> np.ndarray:
    """Maxwellian DGD probability density with the given mean.

    The instantaneous DGD ``τ`` of a fiber is Maxwellian; its mean fixes the
    scale ``a`` via ``<τ> = 2 a sqrt(2/π)``.
    """
    if mean_dgd_ps <= 0:
        raise ValueError("mean_dgd_ps must be > 0")
    a = mean_dgd_ps / (2.0 * sqrt(2.0 / pi))
    t = np.asarray(tau_ps, dtype=float)
    return np.sqrt(2.0 / pi) * t ** 2 * np.exp(-t ** 2 / (2 * a ** 2)) / a ** 3


def sample_dgd_maxwellian(mean_dgd_ps: float, rng: np.random.Generator,
                          size: int | None = None) -> np.ndarray | float:
    """Draw instantaneous DGD(s) from the Maxwellian with the given mean.

    A Maxwellian variate is the magnitude of a 3-vector of i.i.d. Gaussians, so
    this samples the physical DGD directly without emulating sections.
    """
    if mean_dgd_ps <= 0:
        raise ValueError("mean_dgd_ps must be > 0")
    a = mean_dgd_ps / (2.0 * sqrt(2.0 / pi))
    g = rng.standard_normal((3,) if size is None else (size, 3))
    dgd = a * np.sqrt(np.sum(g ** 2, axis=-1))
    return float(dgd) if size is None else dgd


def random_su2(rng: np.random.Generator) -> np.ndarray:
    """A Haar-random SU(2) Jones matrix (uniform on the Poincaré sphere)."""
    v = rng.standard_normal(4)
    v /= np.linalg.norm(v)
    a = v[0] + 1j * v[1]
    b = v[2] + 1j * v[3]
    return np.array([[a, b], [-np.conjugate(b), np.conjugate(a)]], dtype=complex)


@dataclass
class PMDFiber:
    """A PMD emulator: a concatenation of random birefringent sections.

    ``mean_dgd_ps`` sets the target mean DGD; ``n_sections`` random SU(2)
    couplings + fixed retarders reproduce a Maxwellian DGD with that mean.
    """

    mean_dgd_ps: float
    n_sections: int = 50
    seed: int = 0

    def __post_init__(self) -> None:
        if self.mean_dgd_ps < 0:
            raise ValueError("mean_dgd_ps must be non-negative")
        if self.n_sections < 1:
            raise ValueError("n_sections must be >= 1")
        rng = np.random.default_rng(self.seed)
        self._u = [random_su2(rng) for _ in range(self.n_sections)]
        # Per-section DGD so the concatenation's mean DGD matches the target:
        # E[DGD] = tau0 * sqrt(8 n / (3 pi))  (3-D random walk of section vectors).
        self._tau0 = (self.mean_dgd_ps / sqrt(8.0 * self.n_sections / (3.0 * pi))
                      if self.mean_dgd_ps > 0 else 0.0)

    def jones_at(self, omega_rad_per_ps: np.ndarray) -> np.ndarray:
        """Total Jones matrix ``T(ω)`` — shape ``(..., 2, 2)`` over the ω grid."""
        w = np.atleast_1d(np.asarray(omega_rad_per_ps, dtype=float))
        nf = w.shape[0]
        T = np.broadcast_to(np.eye(2, dtype=complex), (nf, 2, 2)).copy()
        phase = np.exp(1j * w * self._tau0 / 2.0)
        for u in self._u:
            D = np.zeros((nf, 2, 2), dtype=complex)
            D[:, 0, 0] = phase
            D[:, 1, 1] = np.conjugate(phase)
            sec = np.einsum("ij,fjk->fik", u, D)      # U @ retarder
            T = np.einsum("fij,fjk->fik", sec, T)
        return T if nf > 1 else T[0]

    def dgd_ps(self, probe_omega: float = 0.0, domega: float = 1e-3) -> float:
        """Measure the DGD (ps) by Jones-Matrix Eigenanalysis around ``probe_omega``."""
        t1 = self.jones_at(np.array([probe_omega]))
        t2 = self.jones_at(np.array([probe_omega + domega]))
        m = t2 @ np.linalg.inv(t1)
        ev = np.linalg.eigvals(m)
        dphi = np.angle(ev[0] / ev[1])
        return abs(dphi) / domega

    def apply(self, field_x: np.ndarray, field_y: np.ndarray, grid: TimeGrid
              ) -> tuple[np.ndarray, np.ndarray]:
        """Propagate a two-polarization field through the PMD emulator."""
        w = grid.omega_rad_per_ps
        T = self.jones_at(w)                          # (nf,2,2)
        ex = np.fft.fft(field_x)
        ey = np.fft.fft(field_y)
        ox = T[:, 0, 0] * ex + T[:, 0, 1] * ey
        oy = T[:, 1, 0] * ex + T[:, 1, 1] * ey
        return np.fft.ifft(ox), np.fft.ifft(oy)


def pdl_jones(pdl_db: float, theta_rad: float = 0.0) -> np.ndarray:
    """A polarization-dependent-loss element (non-unitary Jones matrix).

    Attenuates one axis by ``pdl_db`` relative to the other, with the low-loss
    axis rotated by ``theta_rad``.
    """
    if pdl_db < 0:
        raise ValueError("pdl_db must be non-negative")
    t = 10.0 ** (-pdl_db / 20.0)                       # field transmission ratio
    d = np.array([[1.0, 0.0], [0.0, t]], dtype=complex)
    c, s = np.cos(theta_rad), np.sin(theta_rad)
    r = np.array([[c, -s], [s, c]], dtype=complex)
    return r @ d @ r.T


def apply_jones(jones: np.ndarray, field_x: np.ndarray, field_y: np.ndarray
                ) -> tuple[np.ndarray, np.ndarray]:
    """Apply a constant 2x2 Jones matrix to a two-component field."""
    ox = jones[0, 0] * field_x + jones[0, 1] * field_y
    oy = jones[1, 0] * field_x + jones[1, 1] * field_y
    return ox, oy


def polarization_qber(dgd_ps: float, symbol_rate_baud: float) -> float:
    """QBER a polarization-encoded qubit picks up from PMD depolarization.

    A signal of bandwidth ``~R_s`` passing a DGD ``τ`` loses degree of
    polarization ``DOP ≈ |sinc(R_s τ)|``; the residual depolarization maps to a
    misalignment error ``e = (1 - DOP)/2`` — 0 at zero DGD, rising as the DGD
    approaches a symbol period.  Feed this to the detector misalignment of a
    polarization-based BB84 link.
    """
    if dgd_ps < 0 or symbol_rate_baud <= 0:
        raise ValueError("dgd_ps >= 0 and symbol_rate_baud > 0 required")
    x = symbol_rate_baud * (dgd_ps * 1e-12)            # R_s * tau (dimensionless)
    dop = abs(np.sinc(x))                              # np.sinc(x) = sin(pi x)/(pi x)
    return 0.5 * (1.0 - dop)
