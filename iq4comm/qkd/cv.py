"""Continuous-variable QKD: Gaussian-modulated coherent states (GG02).

Asymptotic secret-key rate for prepare-and-measure GMCS CV-QKD with homodyne
detection and reverse reconciliation, under the standard entangling-cloner
(Gaussian) attack::

    K = beta * I_AB - chi_BE

where ``I_AB`` is the Alice-Bob mutual information, ``chi_BE`` the Holevo bound
on Eve's information about Bob's data, and ``beta`` the reconciliation
efficiency.  All noises are in shot-noise units (SNU).  The channel enters only
through its transmittance ``T`` -- again the :meth:`iqcore.fiber.FiberSpec.
transmissivity` -- so CV-QKD shares the same fiber foundation as DV-QKD and the
classical link.

CV-QKD's coherent (homodyne) detection with a strong local oscillator is an
intrinsically narrow matched filter, which is why it tolerates the broadband
Raman background of classical coexistence better than photon-counting DV-QKD.

Reference: Laudenbach et al., "Continuous-Variable QKD with Gaussian
Modulation -- The Theory of Practical Implementations," Adv. Quantum Technol.
1(1), 2018.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import log2, sqrt

import numpy as np

from iqcore.fiber import FiberSpec, SMF28

__all__ = [
    "holevo_g",
    "CVDetector",
    "cvqkd_homodyne_key_rate",
    "cvqkd_rate_vs_distance",
]


def holevo_g(x: float) -> float:
    """Bosonic entropy ``G(x) = (x+1)log2(x+1) - x log2(x)`` (0 at x=0)."""
    if x <= 0.0:
        return 0.0
    return (x + 1.0) * log2(x + 1.0) - x * log2(x)


@dataclass(frozen=True)
class CVDetector:
    """CV-QKD receiver parameters (shot-noise units).

    Attributes
    ----------
    efficiency:
        Homodyne detector efficiency ``eta_d``.
    electronic_noise:
        Detector electronic noise ``v_el`` (SNU).
    reconciliation_efficiency:
        Reverse-reconciliation efficiency ``beta`` (0-1).
    """

    efficiency: float = 0.6
    electronic_noise: float = 0.05
    reconciliation_efficiency: float = 0.95


def cvqkd_homodyne_key_rate(transmittance: float, *,
                            modulation_variance: float = 4.0,
                            excess_noise: float = 0.01,
                            detector: CVDetector | None = None) -> float:
    """Asymptotic GG02 homodyne reverse-reconciliation key rate (bits/use).

    Parameters
    ----------
    transmittance:
        Channel transmittance ``T`` (0-1).
    modulation_variance:
        Alice's modulation variance ``V_A`` (SNU); the sent thermal state has
        variance ``V = V_A + 1``.
    excess_noise:
        Channel excess noise ``xi`` referred to the input (SNU).
    detector:
        A :class:`CVDetector` (defaults to typical values).
    """
    det = detector or CVDetector()
    t = float(transmittance)
    if t <= 0.0:
        return 0.0
    v = modulation_variance + 1.0
    xi = excess_noise
    eta_d = det.efficiency
    v_el = det.electronic_noise
    beta = det.reconciliation_efficiency

    chi_line = 1.0 / t - 1.0 + xi
    chi_hom = (1.0 - eta_d + v_el) / eta_d
    chi_tot = chi_line + chi_hom / t

    # Alice-Bob mutual information (homodyne).
    i_ab = 0.5 * log2((v + chi_tot) / (1.0 + chi_tot))

    # Holevo bound via symplectic eigenvalues.
    a = v * v * (1.0 - 2.0 * t) + 2.0 * t + t * t * (v + chi_line) ** 2
    b = t * t * (v * chi_line + 1.0) ** 2
    disc = max(a * a - 4.0 * b, 0.0)
    lam1 = sqrt(max(0.5 * (a + sqrt(disc)), 0.0))
    lam2 = sqrt(max(0.5 * (a - sqrt(disc)), 0.0))

    denom = t * (v + chi_tot)
    c = (a * chi_hom + v * sqrt(b) + t * (v + chi_line)) / denom
    d = sqrt(b) * (v + sqrt(b) * chi_hom) / denom
    disc2 = max(c * c - 4.0 * d, 0.0)
    lam3 = sqrt(max(0.5 * (c + sqrt(disc2)), 0.0))
    lam4 = sqrt(max(0.5 * (c - sqrt(disc2)), 0.0))

    chi_be = (holevo_g((lam1 - 1.0) / 2.0) + holevo_g((lam2 - 1.0) / 2.0)
              - holevo_g((lam3 - 1.0) / 2.0) - holevo_g((lam4 - 1.0) / 2.0))

    return max(beta * i_ab - chi_be, 0.0)


def cvqkd_rate_vs_distance(distances_km, *, fiber: FiberSpec = SMF28,
                           modulation_variance: float = 4.0,
                           excess_noise: float = 0.01,
                           detector: CVDetector | None = None):
    """CV-QKD key rate over a range of fiber distances (bits/use)."""
    rates = []
    for dkm in distances_km:
        t = fiber.transmissivity(float(dkm))
        rates.append(cvqkd_homodyne_key_rate(
            t, modulation_variance=modulation_variance,
            excess_noise=excess_noise, detector=detector))
    return np.asarray(rates)
