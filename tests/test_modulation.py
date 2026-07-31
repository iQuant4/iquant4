"""Tests for the digital modulation constellations."""

from __future__ import annotations

import numpy as np
import pytest

from iq4comm.modulation import get_constellation, modulate, demodulate


@pytest.mark.parametrize("fmt,order,k", [
    ("BPSK", 2, 1), ("QPSK", 4, 2), ("16QAM", 16, 4), ("64QAM", 64, 6),
])
def test_order_and_unit_energy(fmt, order, k):
    c = get_constellation(fmt)
    assert c.order == order
    assert c.bits_per_symbol == k
    assert np.mean(np.abs(c.points) ** 2) == pytest.approx(1.0)


@pytest.mark.parametrize("fmt", ["QPSK", "16QAM", "64QAM"])
def test_gray_adjacent_symbols_differ_by_one_bit(fmt):
    c = get_constellation(fmt)
    p, b = c.points, c.symbol_bits
    d = np.abs(p[:, None] - p[None, :])
    dmin = np.min(d[d > 1e-9])
    for i in range(len(p)):
        for j in range(i + 1, len(p)):
            if abs(d[i, j] - dmin) < 1e-6:  # grid-adjacent
                assert int(np.count_nonzero(b[i] != b[j])) == 1


@pytest.mark.parametrize("fmt", ["OOK", "BPSK", "QPSK", "16QAM", "64QAM"])
def test_modulate_demodulate_round_trip(fmt):
    c = get_constellation(fmt)
    rng = np.random.default_rng(0)
    bits = rng.integers(0, 2, size=c.bits_per_symbol * 4000)
    assert np.array_equal(demodulate(modulate(bits, c), c), bits)


def test_unknown_format_raises():
    with pytest.raises(ValueError):
        get_constellation("128QAM")
