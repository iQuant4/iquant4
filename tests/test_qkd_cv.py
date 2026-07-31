"""Validation of the CV-QKD (GG02 homodyne) key-rate model."""

from __future__ import annotations

import numpy as np
import pytest

from iqcore.fiber import SMF28
from iq4comm.qkd import (
    holevo_g,
    CVDetector,
    cvqkd_homodyne_key_rate,
    cvqkd_rate_vs_distance,
    plob_bound_bits,
)


def test_holevo_g_reference():
    assert holevo_g(0.0) == 0.0
    assert holevo_g(1.0) == pytest.approx(2.0)   # (2)log2 2 - 1 log2 1 = 2


def test_rate_positive_and_monotonic():
    d = np.arange(0, 100, 5)
    rates = cvqkd_rate_vs_distance(d)
    assert rates[0] > 0
    assert np.all(np.diff(rates) <= 1e-12)


def test_rate_below_plob():
    for dkm in (0.0, 10.0, 25.0, 50.0, 80.0):
        t = SMF28.transmissivity(dkm)
        assert cvqkd_homodyne_key_rate(t) <= plob_bound_bits(t) + 1e-9


def test_excess_noise_lowers_rate_and_kills_it():
    t = SMF28.transmissivity(25.0)
    rates = [cvqkd_homodyne_key_rate(t, excess_noise=x) for x in (0.0, 0.05, 0.1)]
    assert all(rates[i] >= rates[i + 1] for i in range(len(rates) - 1))
    assert cvqkd_homodyne_key_rate(t, excess_noise=0.5) == 0.0


def test_better_reconciliation_raises_rate():
    t = SMF28.transmissivity(30.0)
    low = CVDetector(reconciliation_efficiency=0.90)
    high = CVDetector(reconciliation_efficiency=0.98)
    assert (cvqkd_homodyne_key_rate(t, detector=high)
            > cvqkd_homodyne_key_rate(t, detector=low))


def test_finite_secure_distance():
    """Asymptotic GMCS reach is finite (finite-key would be shorter)."""
    d = np.arange(0, 300, 1.0)
    rates = cvqkd_rate_vs_distance(d, excess_noise=0.05)
    max_secure = d[np.max(np.where(rates > 0))]
    assert 10 < max_secure < 250
