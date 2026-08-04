"""Discrete-variable QKD: BB84 with infinite-decoy secret-key rate.

Asymptotic secret-key rate (per pulse) for decoy-state BB84 with weak coherent
pulses over a lossy, noisy channel (Lo-Ma-Chen / GLLP)::

    R = q * ( Q1 [1 - H2(e1)] - Q_mu * f * H2(E_mu) )

with the single-photon gain ``Q1`` and error ``e1`` estimated as in the
infinite-decoy limit.  The channel enters only through its transmissivity
``eta`` -- exactly the quantity :meth:`iqcore.fiber.FiberSpec.transmissivity`
produces -- so the QKD layer sits directly on the shared fiber foundation.

The ``background_yield`` argument is the hook for QKD-classical coexistence: any
extra clicks injected into the quantum channel (e.g. spontaneous Raman
scattering from co-propagating DWDM channels) add to the detector background and
degrade the key rate, letting the same formula serve both isolated and
coexistence scenarios.

Reference: Lo, Ma & Chen, "Decoy State Quantum Key Distribution," PRL 94, 2005.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import exp, log, log2, sqrt

import numpy as np

from iqcore.fiber import FiberSpec, SMF28
from .finite_key import FiniteKeyParams

__all__ = [
    "binary_entropy",
    "plob_bound_bits",
    "DetectorModel",
    "bb84_decoy_key_rate",
    "bb84_rate_vs_distance",
]


def binary_entropy(x: float) -> float:
    """Binary Shannon entropy ``H2(x)`` in bits (0 at x=0,1)."""
    if x <= 0.0 or x >= 1.0:
        return 0.0
    return -x * log2(x) - (1.0 - x) * log2(1.0 - x)


def plob_bound_bits(transmissivity: float) -> float:
    """Repeaterless secret-key capacity (PLOB bound) ``-log2(1 - eta)`` bits/use.

    No point-to-point QKD protocol can exceed this; used as a sanity ceiling.
    """
    eta = min(max(transmissivity, 0.0), 1.0 - 1e-15)
    return -log2(1.0 - eta)


@dataclass(frozen=True)
class DetectorModel:
    """Receiver/detector parameters for DV-QKD.

    Attributes
    ----------
    efficiency:
        Detector quantum efficiency (0-1).
    dark_count_prob:
        Dark-count probability per gate, per detector.
    misalignment:
        Optical/basis misalignment error probability ``e_d``.
    error_correction_eff:
        Error-correction inefficiency ``f`` (>= 1; 1.16 is typical).
    """

    efficiency: float = 0.5
    dark_count_prob: float = 1e-6
    misalignment: float = 0.02
    error_correction_eff: float = 1.16


def bb84_decoy_key_rate(transmissivity: float, mu: float = 0.5, *,
                        detector: DetectorModel | None = None,
                        background_yield: float = 0.0,
                        sift_factor: float = 0.5,
                        finite: FiniteKeyParams | None = None) -> float:
    """Asymptotic decoy-state BB84 secret-key rate (bits/pulse).

    Parameters
    ----------
    transmissivity:
        Channel power transmissivity ``eta`` (0-1).
    mu:
        Mean photon number of the signal state.
    detector:
        A :class:`DetectorModel` (defaults to a typical detector).
    background_yield:
        Extra background yield ``Y_bg`` added to the dark-count background -- the
        coexistence hook (e.g. Raman clicks from classical DWDM channels).
    sift_factor:
        ``q`` -- 0.5 for standard BB84 basis sifting, 1.0 for efficient BB84.

    Returns
    -------
    float
        Secret-key rate per pulse (>= 0; 0 when no secure key is possible).
    """
    det = detector or DetectorModel()
    eta_sys = transmissivity * det.efficiency
    e0 = 0.5
    e_d = det.misalignment
    f = det.error_correction_eff

    # Background yield: dark counts (both detectors) plus injected background.
    y0 = 2.0 * det.dark_count_prob + background_yield
    y0 = min(y0, 1.0)

    # Overall gain and QBER of the signal state.
    q_mu = y0 + 1.0 - exp(-eta_sys * mu)
    if q_mu <= 0.0:
        return 0.0
    e_mu = (e0 * y0 + e_d * (1.0 - exp(-eta_sys * mu))) / q_mu

    # Single-photon yield / gain / error (infinite-decoy limit).
    y1 = y0 + eta_sys - y0 * eta_sys
    q1 = mu * exp(-mu) * y1
    e1 = (e0 * y0 + e_d * eta_sys) / y1 if y1 > 0 else 0.5

    if finite is None:
        rate = sift_factor * (q1 * (1.0 - binary_entropy(e1))
                              - q_mu * f * binary_entropy(e_mu))
        return max(rate, 0.0)

    # Finite-key: fluctuation on the single-photon phase error + O(1/N) terms.
    n_pulses = finite.block_size
    eps = finite.eps_security
    n1 = sift_factor * q1 * n_pulses           # sifted single-photon detections
    if n1 < 1.0:
        return 0.0
    t1 = sqrt(log(1.0 / eps) / (2.0 * n1))
    e1_ub = min(e1 + t1, 0.5)
    finite_terms = (6.0 * log2(21.0 / eps) + log2(2.0 / eps)) / n_pulses
    rate = (sift_factor * (q1 * (1.0 - binary_entropy(e1_ub))
                           - q_mu * f * binary_entropy(e_mu)) - finite_terms)
    return max(rate, 0.0)


def bb84_rate_vs_distance(distances_km, mu: float = 0.5, *,
                          fiber: FiberSpec = SMF28,
                          detector: DetectorModel | None = None,
                          background_yield: float = 0.0,
                          sift_factor: float = 0.5):
    """Secret-key rate over a range of fiber distances.

    Returns a numpy array of rates (bits/pulse) aligned with ``distances_km``.
    """
    rates = []
    for d in distances_km:
        eta = fiber.transmissivity(float(d))
        rates.append(bb84_decoy_key_rate(
            eta, mu, detector=detector, background_yield=background_yield,
            sift_factor=sift_factor))
    return np.asarray(rates)
