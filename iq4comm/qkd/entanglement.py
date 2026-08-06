"""Entanglement distribution over fiber (roadmap item 21).

A polarization/time-bin entangled-pair source (e.g. SPDC) placed at the mid-point
sends one photon to each of Alice and Bob over ``L/2`` of fiber. This module
computes the physically distributed **elementary-link Werner fidelity** and the
**BBM92 entanglement-based QKD rate** as functions of distance, from the source
brightness, fiber loss, detector efficiency, and dark counts.

The elementary-link fidelity produced here is exactly the ``segment_fidelity``
that :mod:`iq4comm.qkd.repeater` consumes, so a repeater chain can be built from
a *derived* physical link rather than an assumed fidelity.

Physics
-------
* **Brightness / multi-pair.** A source emitting a mean ``mu`` pairs per pump
  pulse has heralded second-order coherence ``g2(0) ~ 2 mu`` at low ``mu``;
  multi-pair emission lowers the intrinsic state fidelity roughly as
  ``F_src ~ 1 / (1 + mu)`` about the ideal.
* **Distribution.** With a mid-point source each photon crosses ``L/2``; a true
  coincidence needs both detected, probability ``(eta_d * t_half)^2`` with
  ``t_half = T(L/2)``. Dark counts add accidentals that do not fall with loss,
  so the coincidence QBER rises with distance and sets the reach.
* **QBER -> Werner fidelity.** Measured coincidence QBER ``e`` maps to a Werner
  weight ``p = 1 - 2e`` and fidelity ``F = (1 + 3p)/4``.
* **BBM92 key rate.** One-way secret rate ``R = (1/2) R_coinc [1 - f H2(e) -
  H2(e)]^+`` (basis sifting 1/2; ``e_bit = e_phase = e`` for a Werner state).
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from iqcore.fiber import FiberSpec, SMF28
from .dv import DetectorModel, binary_entropy
from .repeater import fidelity_to_p, p_to_fidelity, werner_qber

__all__ = [
    "PairSource",
    "heralded_g2",
    "source_fidelity",
    "coincidence_rate",
    "coincidence_qber",
    "elementary_link_fidelity",
    "bbm92_key_rate",
    "entanglement_reach_km",
    "EntanglementLink",
]


@dataclass(frozen=True)
class PairSource:
    """An entangled-pair source.

    Attributes
    ----------
    mean_pairs:
        Mean pair number ``mu`` per pump pulse (brightness).
    pump_rate_hz:
        Pump repetition rate (Hz); pair-generation rate is ``mu * pump_rate``.
    intrinsic_fidelity:
        Ideal (loss-free, single-pair) state fidelity, capturing source
        imperfections other than multi-pair emission.
    coincidence_window_s:
        Coincidence timing window ``tau_c`` (s) for accidental counting.
    """

    mean_pairs: float = 0.01
    pump_rate_hz: float = 1e9
    intrinsic_fidelity: float = 0.99
    coincidence_window_s: float = 1e-9


def heralded_g2(mu: float) -> float:
    """Heralded second-order coherence ``g2(0) ~ 2 mu`` (multi-pair quality)."""
    return 2.0 * mu


def source_fidelity(source: PairSource) -> float:
    """Emitted-state fidelity including multi-pair degradation, ``F0/(1+mu)`` scaled."""
    ideal = source.intrinsic_fidelity
    # multi-pair pulls the fidelity toward the fully-mixed value 1/4
    f = 0.25 + (ideal - 0.25) / (1.0 + source.mean_pairs)
    return f


def _rates(distance_km, source, detector, fiber):
    t_half = fiber.transmissivity(distance_km / 2.0)          # each arm
    eta = detector.efficiency * t_half
    r_pair = source.mean_pairs * source.pump_rate_hz
    r_true = r_pair * eta ** 2                                # both photons detected
    singles = r_pair * eta + detector.dark_count_prob * source.pump_rate_hz
    # accidental coincidences within the window (dark-involving + multi-pair)
    r_acc = 2.0 * singles ** 2 * source.coincidence_window_s
    return r_true, r_acc


def coincidence_rate(distance_km: float, *, source: PairSource | None = None,
                     detector: DetectorModel | None = None,
                     fiber: FiberSpec = SMF28) -> float:
    """Total coincidence rate (true + accidental), counts/s."""
    source = source or PairSource()
    detector = detector or DetectorModel()
    r_true, r_acc = _rates(distance_km, source, detector, fiber)
    return r_true + r_acc


def coincidence_qber(distance_km: float, *, source: PairSource | None = None,
                     detector: DetectorModel | None = None,
                     fiber: FiberSpec = SMF28) -> float:
    """Coincidence-basis QBER from intrinsic error plus (random) accidentals."""
    source = source or PairSource()
    detector = detector or DetectorModel()
    r_true, r_acc = _rates(distance_km, source, detector, fiber)
    total = r_true + r_acc
    if total <= 0.0:
        return 0.5
    e_intrinsic = werner_qber(source_fidelity(source))
    return (r_true * e_intrinsic + r_acc * 0.5) / total


def elementary_link_fidelity(distance_km: float, *, source: PairSource | None = None,
                             detector: DetectorModel | None = None,
                             fiber: FiberSpec = SMF28) -> float:
    """Distributed Werner fidelity of one elementary link (feeds the repeater)."""
    e = coincidence_qber(distance_km, source=source, detector=detector, fiber=fiber)
    return p_to_fidelity(max(0.0, 1.0 - 2.0 * e))


def bbm92_key_rate(distance_km: float, *, source: PairSource | None = None,
                   detector: DetectorModel | None = None,
                   fiber: FiberSpec = SMF28,
                   f_ec: float = 1.16) -> float:
    """Entanglement-based (BBM92) secret-key rate, bits/s."""
    source = source or PairSource()
    detector = detector or DetectorModel()
    r_coinc = coincidence_rate(distance_km, source=source, detector=detector, fiber=fiber)
    e = coincidence_qber(distance_km, source=source, detector=detector, fiber=fiber)
    secret_fraction = 1.0 - f_ec * binary_entropy(e) - binary_entropy(e)
    return max(0.0, 0.5 * r_coinc * secret_fraction)


def entanglement_reach_km(*, source: PairSource | None = None,
                          detector: DetectorModel | None = None,
                          fiber: FiberSpec = SMF28,
                          f_ec: float = 1.16, max_km: float = 400.0) -> float:
    """Largest distance with a positive BBM92 key rate (bisection)."""
    lo, hi = 0.0, max_km
    if bbm92_key_rate(lo, source=source, detector=detector, fiber=fiber, f_ec=f_ec) <= 0:
        return 0.0
    if bbm92_key_rate(hi, source=source, detector=detector, fiber=fiber, f_ec=f_ec) > 0:
        return hi
    for _ in range(60):
        mid = 0.5 * (lo + hi)
        if bbm92_key_rate(mid, source=source, detector=detector, fiber=fiber, f_ec=f_ec) > 0:
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi)


@dataclass(frozen=True)
class EntanglementLink:
    """Summary of an entanglement-distribution link at one distance."""

    distance_km: float
    coincidence_rate_hz: float
    qber: float
    fidelity: float
    bbm92_rate_bps: float


def evaluate_link(distance_km: float, *, source: PairSource | None = None,
                  detector: DetectorModel | None = None,
                  fiber: FiberSpec = SMF28) -> EntanglementLink:
    """Bundle the distribution observables at one distance."""
    source = source or PairSource()
    detector = detector or DetectorModel()
    return EntanglementLink(
        distance_km=float(distance_km),
        coincidence_rate_hz=coincidence_rate(distance_km, source=source,
                                             detector=detector, fiber=fiber),
        qber=coincidence_qber(distance_km, source=source, detector=detector, fiber=fiber),
        fidelity=elementary_link_fidelity(distance_km, source=source,
                                          detector=detector, fiber=fiber),
        bbm92_rate_bps=bbm92_key_rate(distance_km, source=source,
                                      detector=detector, fiber=fiber),
    )
