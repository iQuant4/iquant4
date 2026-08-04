"""Validation of FEC unified into the format/coexistence chain.

Ties the third lever (channel coding) to the same capacity/QKD tradeoff that
modulation format and pulse-shaping roll-off already drive: a stronger code lets
a format close at a lower launch power (more QKD headroom) while charging its
overhead against the net capacity.
"""

from __future__ import annotations

import pytest

from iq4comm.dsp import get_fec_code
from iq4comm.qkd import (
    format_capacity_bps,
    minimum_launch_for_format_dbm,
    grid_fill_tradeoff,
    protocol_coexistence_key_rate,
)

BAND = 2e12


def test_fec_capacity_charges_overhead():
    """Net capacity with a code is the raw rate times the code rate."""
    fmt, n, d, p = "16QAM", 20, 50.0, -6.0
    raw, _b, closes_raw = format_capacity_bps(fmt, p, n, d)
    sd = get_fec_code("SD-FEC-20%")
    net, _b2, closes_net = format_capacity_bps(fmt, p, n, d, fec=sd)
    assert closes_raw and closes_net
    assert net == pytest.approx(raw * sd.rate)
    assert net < raw                                   # 20% overhead really costs


def test_stronger_fec_closes_at_lower_launch():
    """A stronger code lets 16-QAM close at a lower launch power."""
    fmt, n, d = "16QAM", 20, 60.0
    hd = get_fec_code("HD-FEC-7%")      # threshold 3.8e-3
    sd = get_fec_code("SD-FEC-20%")     # threshold 2.0e-2 (stronger)
    p_hd = minimum_launch_for_format_dbm(fmt, n, d, fec=hd)
    p_sd = minimum_launch_for_format_dbm(fmt, n, d, fec=sd)
    assert p_hd is not None and p_sd is not None
    assert p_sd < p_hd                                  # stronger code -> less power


def test_fec_headroom_raises_qkd_rate():
    """Because a stronger code closes at lower power, the QKD rate at that power is higher."""
    fmt, n, d = "16QAM", 20, 40.0
    hd = get_fec_code("HD-FEC-7%")
    sd = get_fec_code("SD-FEC-20%")
    p_hd = minimum_launch_for_format_dbm(fmt, n, d, fec=hd)
    p_sd = minimum_launch_for_format_dbm(fmt, n, d, fec=sd)
    q_hd = protocol_coexistence_key_rate("dv", d, p_hd, n)
    q_sd = protocol_coexistence_key_rate("dv", d, p_sd, n)
    assert q_sd >= q_hd                                 # lower power -> >= key rate


def test_grid_fill_accepts_fec_and_reduces_capacity():
    """Passing a code through grid_fill_tradeoff yields net (overhead-charged) capacity."""
    sd = get_fec_code("SD-FEC-20%")
    raw = grid_fill_tradeoff(40.0, BAND, -10.0, rolloffs=(0.2,), fmt="16QAM")
    net = grid_fill_tradeoff(40.0, BAND, -10.0, rolloffs=(0.2,), fmt="16QAM", fec=sd)
    r, nrec = raw[0], net[0]
    assert r.n_channels == nrec.n_channels
    if r.classical_closes and nrec.classical_closes:
        assert nrec.classical_capacity_bps == pytest.approx(
            r.classical_capacity_bps * sd.rate)
    # QKD rate is unaffected by the coding choice at fixed launch/channels.
    assert nrec.secret_key_rate == pytest.approx(r.secret_key_rate)


def test_no_fec_matches_legacy_constant():
    """fec=None reproduces the hard-coded 3.8e-3 behaviour exactly (no overhead)."""
    fmt, n, d, p = "QPSK", 20, 50.0, -10.0
    raw, ber, closes = format_capacity_bps(fmt, p, n, d)          # min_ber=3.8e-3
    assert closes == (ber <= 3.8e-3)
    if closes:
        assert raw == pytest.approx(n * 32e9 * 2)                 # k=2, no rate factor
