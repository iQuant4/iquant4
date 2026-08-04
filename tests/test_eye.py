"""Validation of the eye-diagram and Q-factor signal-quality metrics."""

from __future__ import annotations

import numpy as np
import pytest

from iq4comm.dsp import (
    q_factor,
    q_factor_db,
    q_to_ber,
    ber_to_q,
    build_eye,
    shaped_nrz_waveform,
    ber_theory,
)


def test_q_factor_formula():
    assert q_factor(1.0, 0.0, 0.1, 0.1) == pytest.approx(5.0)
    assert q_factor_db(10.0) == pytest.approx(20.0)
    assert q_factor(1.0, 0.0, 0.0, 0.0) == float("inf")   # noiseless -> infinite Q


def test_q_ber_roundtrip():
    for q in (3.0, 6.0, 7.03):                             # 7.03 ~ BER 1e-12
        assert ber_to_q(q_to_ber(q)) == pytest.approx(q, rel=1e-6)
    assert q_to_ber(7.034) == pytest.approx(1e-12, rel=0.05)


def test_q_to_ber_matches_bpsk_theory():
    """For an ideal binary channel, Q = sqrt(2 Eb/N0) reproduces the BPSK BER."""
    ebn0_db = 8.0
    ebn0 = 10 ** (ebn0_db / 10)
    q = np.sqrt(2 * ebn0)
    assert q_to_ber(q) == pytest.approx(ber_theory("BPSK", ebn0_db), rel=1e-9)


def test_noiseless_eye_is_wide_open():
    rng = np.random.default_rng(0)
    bits = rng.integers(0, 2, 400)
    wf = shaped_nrz_waveform(bits, sps=16, snr_db=None)
    eye = build_eye(wf, 16)
    assert eye.eye_amplitude == pytest.approx(1.0, abs=0.05)   # levels 0 and 1
    assert eye.q_factor > 50                                    # essentially closed noise
    assert eye.eye_opening_ratio > 0.9


def test_higher_snr_gives_higher_q_and_lower_ber():
    rng = np.random.default_rng(1)
    bits = rng.integers(0, 2, 4000)
    q_hi = build_eye(shaped_nrz_waveform(bits, 16, snr_db=22.0, rng=rng), 16).q_factor
    q_lo = build_eye(shaped_nrz_waveform(bits, 16, snr_db=12.0, rng=rng), 16).q_factor
    assert q_hi > q_lo > 0
    assert q_to_ber(q_hi) < q_to_ber(q_lo)


def test_measured_q_tracks_the_set_snr():
    """The eye Q of an OOK signal is ~ half the amplitude/sigma ratio (10^(snr/20)/2)."""
    rng = np.random.default_rng(2)
    bits = rng.integers(0, 2, 8000)
    snr_db = 18.0
    eye = build_eye(shaped_nrz_waveform(bits, 16, snr_db=snr_db, rng=rng), 16)
    expected_q = 10 ** (snr_db / 20.0) / 2.0                   # amp/(sigma1+sigma0)
    assert eye.q_factor == pytest.approx(expected_q, rel=0.2)


def test_decision_threshold_between_levels():
    rng = np.random.default_rng(3)
    bits = rng.integers(0, 2, 2000)
    eye = build_eye(shaped_nrz_waveform(bits, 16, snr_db=16.0, rng=rng), 16)
    assert eye.mu0 < eye.decision_threshold < eye.mu1


def test_eye_shape_and_errors():
    rng = np.random.default_rng(4)
    bits = rng.integers(0, 2, 200)
    eye = build_eye(shaped_nrz_waveform(bits, 16), 16, symbols_per_trace=2)
    assert eye.traces.shape[1] == 2 * 16
    with pytest.raises(ValueError):
        build_eye(np.zeros(10), 1)                            # sps < 2
    with pytest.raises(ValueError):
        ber_to_q(0.9)                                         # ber out of range
