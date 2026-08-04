"""Validation of the modulation-format impact on QKD coexistence."""

from __future__ import annotations

import pytest

from iq4comm.qkd import (
    format_ber,
    format_capacity_bps,
    minimum_launch_for_format_dbm,
    format_qkd_tradeoff,
)


def test_higher_order_needs_higher_snr():
    """At a fixed SNR, a higher-order format has a worse BER."""
    snr_db = 14.0
    assert format_ber("64QAM", snr_db) > format_ber("16QAM", snr_db)
    assert format_ber("16QAM", snr_db) > format_ber("QPSK", snr_db)


def test_higher_order_needs_more_launch_power():
    """Closing 64-QAM requires a higher launch power than QPSK at equal reach."""
    d, n = 50.0, 20
    p_qpsk = minimum_launch_for_format_dbm("QPSK", n, d)
    p_16 = minimum_launch_for_format_dbm("16QAM", n, d)
    p_64 = minimum_launch_for_format_dbm("64QAM", n, d)
    assert p_qpsk is not None and p_16 is not None and p_64 is not None
    assert p_64 > p_16 > p_qpsk


def test_capacity_ordering_when_all_close():
    """At a high launch where all close, capacity rises with the format order."""
    d, n, p = 50.0, 20, 2.0
    caps = {f: format_capacity_bps(f, p, n, d)[0]
            for f in ("QPSK", "16QAM", "64QAM")}
    assert caps["64QAM"] > caps["16QAM"] > caps["QPSK"] > 0


def test_qkd_rate_is_format_independent_at_fixed_launch():
    """Every format sees the same QKD rate at a given launch power (Raman ~ power)."""
    impacts = format_qkd_tradeoff(50.0, 20, -14.0)
    skrs = {i.secret_key_rate for i in impacts}
    assert len(skrs) == 1                      # identical across formats


def test_format_that_fails_delivers_zero_capacity():
    """A format that cannot close the link at a low launch delivers no capacity."""
    cap, ber, closes = format_capacity_bps("64QAM", -26.0, 20, 50.0)
    assert not closes and cap == 0.0 and ber > 3.8e-3
