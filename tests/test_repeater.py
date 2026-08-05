"""Validation of entanglement distribution and quantum-repeater models."""

from __future__ import annotations

import numpy as np
import pytest

from iqcore.fiber import SMF28
from iq4comm.qkd import (
    fidelity_to_p,
    p_to_fidelity,
    swap_fidelity,
    chained_fidelity,
    werner_qber,
    entanglement_key_fraction,
    direct_plob_rate,
    repeater_secret_key_rate,
    optimal_segment_count,
    repeater_advantage_distance,
)


def test_fidelity_p_roundtrip():
    for f in (0.25, 0.5, 0.8, 0.95, 1.0):
        assert p_to_fidelity(fidelity_to_p(f)) == pytest.approx(f)
    assert fidelity_to_p(1.0) == pytest.approx(1.0)      # pure state -> p=1
    assert fidelity_to_p(0.25) == pytest.approx(0.0)     # maximally mixed -> p=0


def test_swapping_degrades_fidelity():
    """Entanglement swapping of imperfect states lowers fidelity (p multiplies)."""
    f = swap_fidelity(0.95, 0.95)
    assert 0.25 < f < 0.95
    assert swap_fidelity(1.0, 0.9) == pytest.approx(0.9)  # perfect relay is transparent
    assert swap_fidelity(1.0, 1.0) == pytest.approx(1.0)


def test_chained_fidelity_monotone_decreasing():
    fs = [chained_fidelity(0.98, n) for n in (1, 2, 4, 8, 16)]
    assert all(b < a for a, b in zip(fs, fs[1:]))
    assert fs[0] == pytest.approx(0.98)
    assert all(f > 0.25 for f in fs)                     # stays a valid Werner state


def test_key_fraction_positive_high_fidelity_zero_low():
    assert entanglement_key_fraction(0.99) > 0.5
    assert entanglement_key_fraction(0.95) > 0.0
    assert entanglement_key_fraction(0.75) == 0.0        # too noisy -> no key
    assert werner_qber(1.0) == pytest.approx(0.0)


def test_repeater_beats_direct_at_long_distance():
    """At long distance the memory-assisted repeater exceeds the PLOB bound."""
    d = 500.0
    plob = direct_plob_rate(d)
    best = optimal_segment_count(d)
    assert best.secret_key_rate > plob
    assert best.beats_plob
    assert best.n_segments > 1


def test_direct_wins_at_short_distance():
    """At short distance the repeaterless bound is higher (no swap penalty)."""
    d = 20.0
    plob = direct_plob_rate(d)
    best = optimal_segment_count(d)
    assert plob > best.secret_key_rate                   # PLOB unbeaten up close


def test_optimal_segments_grow_with_distance():
    n_short = optimal_segment_count(80.0).n_segments
    n_long = optimal_segment_count(600.0).n_segments
    assert n_long > n_short >= 1


def test_advantage_distance_is_finite_and_ordered():
    d_cross = repeater_advantage_distance()
    assert 0.0 < d_cross < 1000.0
    # below the crossover PLOB wins; above it the repeater wins
    assert not optimal_segment_count(d_cross - 20).beats_plob
    assert optimal_segment_count(d_cross + 40).beats_plob


def test_n1_repeater_has_no_swap_penalty():
    """A single segment is a direct entangled link: rate = eta(L)*key_fraction."""
    d = 100.0
    r1 = repeater_secret_key_rate(d, 1, swap_success=0.5)
    expected = SMF28.transmissivity(d) * entanglement_key_fraction(0.98)
    assert r1 == pytest.approx(expected, rel=1e-9)


def test_poor_fidelity_prevents_advantage():
    """Fidelity, not swap loss, is the real limiter: too-noisy segments yield no key.

    A constant swap-success penalty is always eventually beaten (halving the loss
    exponent outruns any constant against an exponentially small PLOB), but if the
    per-segment fidelity is too low every segment count gives zero secret fraction,
    so the repeater never beats the (small but positive) PLOB bound.
    """
    assert repeater_advantage_distance(segment_fidelity=0.80) == 0.0
    # ...whereas a lossy-but-clean swap still wins eventually (fidelity intact).
    assert repeater_advantage_distance(swap_success=0.05, segment_fidelity=0.99) > 0.0
