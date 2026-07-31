"""Validation of the DV-QKD (decoy-state BB84) key-rate model."""

from __future__ import annotations

import numpy as np
import pytest

from iqcore.fiber import SMF28
from iq4comm.qkd import (
    binary_entropy,
    plob_bound_bits,
    DetectorModel,
    bb84_decoy_key_rate,
    bb84_rate_vs_distance,
)


def test_binary_entropy_reference():
    assert binary_entropy(0.0) == 0.0
    assert binary_entropy(1.0) == 0.0
    assert binary_entropy(0.5) == pytest.approx(1.0)
    assert binary_entropy(0.11) == pytest.approx(0.4999, abs=1e-3)


def test_rate_positive_at_short_distance_and_decreasing():
    d = np.arange(0, 260, 10)
    rates = bb84_rate_vs_distance(d)
    assert rates[0] > 0
    # Monotonically non-increasing with distance.
    assert np.all(np.diff(rates) <= 1e-12)


def test_finite_secure_distance_in_expected_range():
    """BB84 over SMF-28 secures out to ~150-260 km, then hits zero."""
    d = np.arange(0, 400, 2)
    rates = bb84_rate_vs_distance(d)
    max_secure = d[np.max(np.where(rates > 0))]
    assert 120 <= max_secure <= 320


def test_rate_never_exceeds_plob_bound():
    """The finite BB84 rate must stay below the repeaterless capacity."""
    for dkm in (0.0, 20.0, 50.0, 100.0, 150.0):
        eta = SMF28.transmissivity(dkm)
        r = bb84_decoy_key_rate(eta)
        assert r <= plob_bound_bits(eta) + 1e-12


def test_background_reduces_rate_and_reach():
    """Injected background (coexistence hook) lowers rate and secure distance."""
    d = np.arange(0, 400, 2)
    clean = bb84_rate_vs_distance(d)
    noisy = bb84_rate_vs_distance(d, background_yield=1e-4)
    # Everywhere no better, and strictly worse where there was key.
    assert np.all(noisy <= clean + 1e-15)
    reach_clean = d[np.max(np.where(clean > 0))]
    reach_noisy = d[np.max(np.where(noisy > 0))]
    assert reach_noisy < reach_clean


def test_lower_dark_counts_extend_reach():
    d = np.arange(0, 500, 2)
    good = DetectorModel(dark_count_prob=1e-7)
    poor = DetectorModel(dark_count_prob=1e-5)
    reach_good = d[np.max(np.where(bb84_rate_vs_distance(d, detector=good) > 0))]
    reach_poor = d[np.max(np.where(bb84_rate_vs_distance(d, detector=poor) > 0))]
    assert reach_good > reach_poor
