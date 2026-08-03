"""Validation of the QKD-classical DWDM coexistence model."""

from __future__ import annotations

import numpy as np
import pytest

from iqcore.fiber import SMF28
from iq4comm.qkd import (
    raman_background_yield,
    coexistence_dv_key_rate,
    classical_capacity_bps,
    coexistence_curve,
    bb84_decoy_key_rate,
)


def test_raman_background_scales_with_power():
    d = 50.0
    b1 = raman_background_yield(1e-3, d)
    b2 = raman_background_yield(2e-3, d)
    assert b2 == pytest.approx(2 * b1)          # linear in classical power
    assert raman_background_yield(0.0, d) == 0.0


def test_zero_classical_power_recovers_isolated_qkd():
    d = 50.0
    coex = coexistence_dv_key_rate(d, -np.inf, 20)  # -inf dBm -> 0 W
    iso = bb84_decoy_key_rate(SMF28.transmissivity(d))
    assert coex == pytest.approx(iso)


def test_more_classical_power_lowers_key_rate():
    d = 50.0  # points inside the calibrated secure window (boundary ~ -11 dBm)
    rates = [coexistence_dv_key_rate(d, p, 20) for p in (-20, -16, -13)]
    # Non-increasing as classical power rises.
    assert all(rates[i] >= rates[i + 1] for i in range(len(rates) - 1))
    # High enough classical power extinguishes the key.
    assert coexistence_dv_key_rate(d, 0.0, 20) == 0.0


def test_more_channels_lowers_key_rate():
    d = 50.0  # -16 dBm: both channel counts still secure, more channels -> lower
    assert coexistence_dv_key_rate(d, -16.0, 40) < coexistence_dv_key_rate(d, -16.0, 10)


def test_classical_capacity_positive_with_interior_gn_optimum():
    grid = np.arange(-25.0, 12.0, 1.0)
    caps = np.array([classical_capacity_bps(p, 20, 50.0) for p in grid])
    assert np.all(caps > 0)
    # A Gaussian-noise optimum: the peak is interior, not at either extreme.
    peak = int(np.argmax(caps))
    assert 0 < peak < len(caps) - 1


def test_secure_window_and_tradeoff():
    """A secure launch-power window exists; past it, the key dies but classical
    capacity remains -- the coexistence tradeoff."""
    grid = np.arange(-20, 10, 1.0)
    pts = coexistence_curve(50.0, 20, grid)
    secure = [p for p in pts if p.secure and p.classical_capacity_bps > 0]
    assert len(secure) > 0
    # Key rate is non-increasing in launch power.
    skr = [p.secret_key_rate for p in pts]
    assert all(skr[i] >= skr[i + 1] for i in range(len(skr) - 1))
    # At the highest power the key is dead but classical capacity is still large.
    assert pts[-1].secret_key_rate == 0.0
    assert pts[-1].classical_capacity_bps > 1e12
