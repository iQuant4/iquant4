"""Entanglement distribution and quantum repeaters: beating the direct-reach limit.

The coexistence window and every direct QKD curve in this platform share one
hard ceiling: the **PLOB bound**, ``−log2(1−η)`` bits per use, which falls off
*exponentially* with distance because the transmissivity does. No amount of
launch-power or protocol cleverness escapes it on a point-to-point link — it is
why the coexistence window pinches shut. The way past it is a **quantum
repeater**: cut the link into segments, distribute entanglement on each, store it
in quantum memories, and fuse the segments with **entanglement swapping** so the
loss no longer accumulates in one exponential.

This module models that chain on the shared fiber foundation:

* **Entanglement + Werner states.** A noisy entangled pair is a Werner state,
  summarised by its fidelity ``F`` (or the depolarising weight ``p = (4F−1)/3``).
* **Entanglement swapping.** Fusing two Werner segments multiplies their weights,
  ``p_out = p1·p2`` — fidelity degrades with every swap, so more segments trade
  reach for quality.
* **Repeater rate.** With memories, each segment is re-attempted independently and
  the end-to-end rate is set by a *single* segment's transmissivity ``η(L/n)``
  (times the swap-chain efficiency), not by ``η(L)`` — converting exponential
  loss into a polynomial one and eventually beating PLOB.

The payoff read-outs: :func:`repeater_secret_key_rate`, the optimal segment count
:func:`optimal_segment_count` (grows with distance, capped by fidelity decay), and
:func:`repeater_advantage_distance` — where a repeater overtakes the repeaterless
bound.

References: Briegel et al., PRL 81, 5932 (1998); Sangouard et al., RMP 83, 33
(2011); Pirandola et al. (PLOB), Nat. Commun. 8, 15043 (2017).
"""

from __future__ import annotations

from dataclasses import dataclass

from iqcore.fiber import FiberSpec, SMF28
from .dv import binary_entropy, plob_bound_bits

__all__ = [
    "fidelity_to_p",
    "p_to_fidelity",
    "swap_fidelity",
    "chained_fidelity",
    "werner_qber",
    "entanglement_key_fraction",
    "direct_plob_rate",
    "repeater_secret_key_rate",
    "optimal_segment_count",
    "repeater_advantage_distance",
    "RepeaterLink",
]


def fidelity_to_p(fidelity: float) -> float:
    """Werner depolarising weight ``p = (4F − 1) / 3`` from the fidelity."""
    return (4.0 * fidelity - 1.0) / 3.0


def p_to_fidelity(p: float) -> float:
    """Werner fidelity ``F = (1 + 3p) / 4`` from the depolarising weight."""
    return (1.0 + 3.0 * p) / 4.0


def swap_fidelity(f1: float, f2: float) -> float:
    """Fidelity after entanglement-swapping two Werner states: ``p_out = p1·p2``."""
    return p_to_fidelity(fidelity_to_p(f1) * fidelity_to_p(f2))


def chained_fidelity(segment_fidelity: float, n_segments: int) -> float:
    """End-to-end fidelity of ``n_segments`` swapped Werner links (``p^n``)."""
    if n_segments < 1:
        raise ValueError("n_segments must be >= 1")
    return p_to_fidelity(fidelity_to_p(segment_fidelity) ** n_segments)


def werner_qber(fidelity: float) -> float:
    """Average QBER of a Werner state: ``e = (1 − p) / 2`` with ``p = (4F−1)/3``."""
    return 0.5 * (1.0 - fidelity_to_p(fidelity))


def entanglement_key_fraction(fidelity: float) -> float:
    """Asymptotic BBM92/six-state secret fraction ``max(0, 1 − 2 H2(e))``."""
    e = werner_qber(fidelity)
    return max(0.0, 1.0 - 2.0 * binary_entropy(e))


def direct_plob_rate(distance_km: float, *, fiber: FiberSpec = SMF28) -> float:
    """Repeaterless secret-key ceiling (PLOB) at a distance, bits/use."""
    return plob_bound_bits(fiber.transmissivity(distance_km))


@dataclass(frozen=True)
class RepeaterLink:
    """Result of a repeater evaluation at one segment count."""

    distance_km: float
    n_segments: int
    end_to_end_fidelity: float
    secret_key_rate: float
    beats_plob: bool


def repeater_secret_key_rate(distance_km: float, n_segments: int, *,
                             fiber: FiberSpec = SMF28,
                             segment_fidelity: float = 0.98,
                             swap_success: float = 0.5,
                             source_efficiency: float = 1.0) -> float:
    """Memory-assisted repeater secret-key rate (relative bits/use).

    With quantum memories each of the ``n_segments`` is heralded independently, so
    the end-to-end rate is limited by *one* segment's transmissivity
    ``η(L/n)`` — not ``η(L)`` — times the ``(n−1)``-swap-chain efficiency and the
    secret fraction of the chained Werner fidelity::

        R ≈ source_eff · η(L/n) · swap_success^(n−1) · [1 − 2 H2(e_end)].

    ``n_segments = 1`` reduces to a direct entangled link (no swap).
    """
    if n_segments < 1:
        raise ValueError("n_segments must be >= 1")
    eta_seg = fiber.transmissivity(distance_km / n_segments)
    f_end = chained_fidelity(segment_fidelity, n_segments)
    frac = entanglement_key_fraction(f_end)
    return (source_efficiency * eta_seg * swap_success ** (n_segments - 1) * frac)


def optimal_segment_count(distance_km: float, *, fiber: FiberSpec = SMF28,
                          segment_fidelity: float = 0.98,
                          swap_success: float = 0.5,
                          source_efficiency: float = 1.0,
                          max_segments: int = 64) -> RepeaterLink:
    """Segment count maximising the repeater rate at a distance.

    Scans ``n`` and returns the best :class:`RepeaterLink`; the optimum grows with
    distance (more segments shorten each hop) until fidelity decay caps it.
    """
    best = None
    for n in range(1, max_segments + 1):
        r = repeater_secret_key_rate(
            distance_km, n, fiber=fiber, segment_fidelity=segment_fidelity,
            swap_success=swap_success, source_efficiency=source_efficiency)
        if best is None or r > best[1]:
            best = (n, r)
    n_opt, r_opt = best
    f_end = chained_fidelity(segment_fidelity, n_opt)
    return RepeaterLink(distance_km, n_opt, f_end, r_opt,
                        r_opt > direct_plob_rate(distance_km, fiber=fiber))


def repeater_advantage_distance(*, fiber: FiberSpec = SMF28,
                                segment_fidelity: float = 0.98,
                                swap_success: float = 0.5,
                                source_efficiency: float = 1.0,
                                search_max_km: float = 1000.0) -> float:
    """Shortest distance at which the optimal repeater beats the PLOB bound.

    Returns 0.0 if it never wins in the search range (e.g. fidelity/swap too poor).
    """
    lo, hi = 1.0, search_max_km

    def wins(d):
        return optimal_segment_count(
            d, fiber=fiber, segment_fidelity=segment_fidelity,
            swap_success=swap_success, source_efficiency=source_efficiency).beats_plob

    if wins(lo):
        return lo
    if not wins(hi):
        return 0.0
    for _ in range(40):
        mid = 0.5 * (lo + hi)
        if wins(mid):
            hi = mid
        else:
            lo = mid
    return hi
