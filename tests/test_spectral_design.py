"""Validation of the roll-off -> capacity/QKD tie-in over a fixed optical band."""

from __future__ import annotations

import pytest

from iq4comm.qkd import (
    channels_in_band,
    grid_fill_tradeoff,
    best_rolloff_for_key_rate,
)

BAND = 4e12          # 4 THz optical window
RS = 32e9


def test_lower_rolloff_fits_more_channels():
    n_sharp = channels_in_band(BAND, RS, beta=0.05)
    n_soft = channels_in_band(BAND, RS, beta=0.5)
    assert n_sharp > n_soft > 0


def test_guard_band_reduces_channel_count():
    n0 = channels_in_band(BAND, RS, beta=0.2, guard_fraction=0.0)
    n1 = channels_in_band(BAND, RS, beta=0.2, guard_fraction=0.25)
    assert n1 < n0


def test_tighter_rolloff_raises_capacity_and_total_power():
    pts = grid_fill_tradeoff(50.0, BAND, -8.0, rolloffs=(0.05, 0.5),
                             fmt="16QAM")
    sharp = next(p for p in pts if p.beta == 0.05)
    soft = next(p for p in pts if p.beta == 0.5)
    assert sharp.n_channels > soft.n_channels
    if sharp.classical_closes and soft.classical_closes:
        assert sharp.classical_capacity_bps > soft.classical_capacity_bps
    assert sharp.total_launch_dbm > soft.total_launch_dbm     # more channels -> more power


def test_tighter_rolloff_lowers_qkd_rate():
    """More channels -> more total power -> more Raman -> lower secret-key rate."""
    pts = grid_fill_tradeoff(50.0, BAND, -10.0, rolloffs=(0.05, 0.5),
                             fmt="16QAM")
    sharp = next(p for p in pts if p.beta == 0.05)
    soft = next(p for p in pts if p.beta == 0.5)
    assert sharp.secret_key_rate <= soft.secret_key_rate


def test_qkd_rate_monotonic_in_rolloff():
    """Secret-key rate is non-decreasing as roll-off widens (fewer channels)."""
    pts = grid_fill_tradeoff(60.0, BAND, -12.0,
                             rolloffs=(0.05, 0.1, 0.2, 0.35, 0.5, 0.75, 1.0))
    skr = [p.secret_key_rate for p in pts]
    assert all(b >= a - 1e-18 for a, b in zip(skr, skr[1:]))


def test_best_rolloff_respects_key_rate_floor():
    """The chosen point meets the floor and no feasible point beats its capacity."""
    floor_rate = 1e-8
    pts = grid_fill_tradeoff(50.0, BAND, -12.0)
    best = best_rolloff_for_key_rate(50.0, BAND, -12.0, floor_rate)
    feasible = [p for p in pts if p.classical_closes and p.secret_key_rate >= floor_rate]
    if feasible:
        assert best is not None
        assert best.secret_key_rate >= floor_rate
        assert best.classical_capacity_bps == max(p.classical_capacity_bps for p in feasible)
    else:
        assert best is None


def test_impossible_floor_returns_none():
    assert best_rolloff_for_key_rate(50.0, BAND, 0.0, 1e9) is None
