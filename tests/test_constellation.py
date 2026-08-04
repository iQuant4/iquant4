"""Validation of the constellation-diagram / EVM signal-quality metrics."""

from __future__ import annotations

import numpy as np
import pytest

from iq4comm.dsp import (
    evm_rms,
    mer_db,
    evm_to_snr_db,
    snr_db_to_evm,
    evm_to_ber,
    received_constellation,
    ber_theory,
)


def test_perfect_constellation_has_zero_evm():
    ref = np.array([1 + 1j, -1 + 1j, -1 - 1j, 1 - 1j]) / np.sqrt(2)
    assert evm_rms(ref, ref) == pytest.approx(0.0)
    assert mer_db(ref, ref) == float("inf")


def test_evm_snr_roundtrip():
    for snr in (6.0, 12.0, 20.0):
        assert evm_to_snr_db(snr_db_to_evm(snr)) == pytest.approx(snr)


def test_measured_evm_recovers_set_snr():
    """EVM of a simulated constellation recovers the SNR it was built at."""
    rng = np.random.default_rng(0)
    for snr in (10.0, 16.0, 22.0):
        cd = received_constellation("16QAM", snr, n_symbols=20000, rng=rng)
        assert cd.snr_db == pytest.approx(snr, abs=0.4)     # MER ~ set SNR
        assert cd.mer_db == pytest.approx(cd.snr_db)


def test_evm_to_ber_matches_theory():
    """BER predicted from EVM equals the closed-form BER at that SNR."""
    for fmt in ("QPSK", "16QAM", "64QAM"):
        k = {"QPSK": 2, "16QAM": 4, "64QAM": 6}[fmt]
        snr_db = 18.0
        evm = snr_db_to_evm(snr_db)
        expected = ber_theory(fmt, snr_db - 10 * np.log10(k))
        assert evm_to_ber(evm, fmt) == pytest.approx(expected, rel=1e-9)


def test_higher_order_format_worse_ber_at_fixed_evm():
    """At the same EVM, a denser constellation has a higher BER."""
    evm = snr_db_to_evm(18.0)
    assert evm_to_ber(evm, "64QAM") > evm_to_ber(evm, "16QAM") > evm_to_ber(evm, "QPSK")


def test_lower_snr_widens_the_cloud():
    """A noisier channel gives a larger EVM (more scattered constellation)."""
    rng = np.random.default_rng(1)
    hi = received_constellation("16QAM", 22.0, n_symbols=8000, rng=rng).evm_rms
    lo = received_constellation("16QAM", 10.0, n_symbols=8000, rng=rng).evm_rms
    assert lo > hi > 0


def test_evm_shape_mismatch_raises():
    with pytest.raises(ValueError):
        evm_rms(np.zeros(4), np.zeros(5))
