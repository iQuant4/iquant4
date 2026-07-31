"""BER: Monte-Carlo agreement with closed-form theory, and the OSNR bridge."""

from __future__ import annotations

import numpy as np
import pytest

from iq4comm.dsp import (
    ber_theory,
    monte_carlo_ber,
    osnr_db_to_ebn0_db,
    q_function,
)


def test_q_function_reference_values():
    assert q_function(0.0) == pytest.approx(0.5)
    assert q_function(1.0) == pytest.approx(0.158655, abs=1e-5)
    assert q_function(3.0) == pytest.approx(1.349898e-3, abs=1e-7)


def test_bpsk_qpsk_theory_equal():
    for ebn0 in (0.0, 5.0, 10.0):
        assert ber_theory("BPSK", ebn0) == pytest.approx(ber_theory("QPSK", ebn0))


@pytest.mark.parametrize("fmt,points,nbits,tol", [
    ("BPSK", (0, 2, 4, 6), 2_000_000, 0.12),
    ("QPSK", (0, 2, 4, 6), 2_000_000, 0.12),
    ("16QAM", (10, 12, 14), 4_000_000, 0.15),
    ("64QAM", (16, 18), 6_000_000, 0.20),
])
def test_monte_carlo_matches_theory(fmt, points, nbits, tol):
    rng = np.random.default_rng(42)
    for ebn0 in points:
        mc = monte_carlo_ber(fmt, ebn0, num_bits=nbits, rng=rng).ber
        th = ber_theory(fmt, ebn0)
        assert mc == pytest.approx(th, rel=tol)


def test_ber_monotonic_decreasing():
    prev = 1.0
    for ebn0 in range(0, 12, 2):
        cur = ber_theory("16QAM", ebn0)
        assert cur < prev
        prev = cur


def test_osnr_to_ebn0_bridge():
    # 5 dB more OSNR -> 5 dB more Eb/N0 (linear scaling).
    e1 = osnr_db_to_ebn0_db(15.0, 32e9, bits_per_symbol=2)
    e2 = osnr_db_to_ebn0_db(20.0, 32e9, bits_per_symbol=2)
    assert (e2 - e1) == pytest.approx(5.0, abs=1e-9)
    # Higher OSNR -> lower BER.
    assert ber_theory("QPSK", e2) < ber_theory("QPSK", e1)
