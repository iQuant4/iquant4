"""Validation of coherent carrier-phase and timing recovery."""

from __future__ import annotations

import numpy as np
import pytest

from iq4comm.modulation import get_constellation, modulate
from iq4comm.dsp import (
    laser_phase_noise,
    apply_frequency_offset,
    estimate_frequency_offset,
    viterbi_viterbi_cpe,
    bps_cpe,
    residual_phase_variance,
    gardner_ted,
    oerder_meyr_timing,
)

RS = 32e9


def _qpsk(n, rng):
    c = get_constellation("QPSK")
    bits = rng.integers(0, 2, n * 2)
    return modulate(bits, c)


def test_phase_noise_variance_scales_with_linewidth():
    rng = np.random.default_rng(0)
    n = 200000
    v_lo = np.var(np.diff(laser_phase_noise(n, 1e5, RS, rng)))
    v_hi = np.var(np.diff(laser_phase_noise(n, 1e6, RS, rng)))
    assert v_hi == pytest.approx(10 * v_lo, rel=0.1)          # 10x linewidth -> 10x var
    assert v_lo == pytest.approx(2 * np.pi * 1e5 / RS, rel=0.1)


def test_frequency_offset_estimator_recovers_known_offset():
    rng = np.random.default_rng(1)
    s = _qpsk(20000, rng)
    for df in (50e6, -120e6, 300e6):
        r = apply_frequency_offset(s, df, RS)
        est = estimate_frequency_offset(r, 4, RS)
        assert est == pytest.approx(df, abs=2e6)


def test_viterbi_viterbi_removes_constant_phase():
    rng = np.random.default_rng(2)
    s = _qpsk(4000, rng)
    r = s * np.exp(1j * 0.9)                                  # constant phase offset
    comp, _ = viterbi_viterbi_cpe(r, m=4, window=21)
    # evaluate on the steady-state region (exclude the filter transient at the ends)
    assert residual_phase_variance(comp[50:-50], s[50:-50]) < 1e-3


def test_viterbi_viterbi_tracks_phase_noise():
    rng = np.random.default_rng(3)
    s = _qpsk(20000, rng)
    ph = laser_phase_noise(len(s), 1e5, RS, rng)
    r = s * np.exp(1j * ph)
    comp, _ = viterbi_viterbi_cpe(r, m=4, window=31)
    before = residual_phase_variance(r[100:-100], s[100:-100])
    after = residual_phase_variance(comp[100:-100], s[100:-100])
    assert after < before / 10                               # large reduction


def test_bps_recovers_phase_on_16qam():
    rng = np.random.default_rng(4)
    c = get_constellation("16QAM")
    s = modulate(rng.integers(0, 2, 4000 * 4), c)
    r = s * np.exp(1j * 0.5)
    comp, _ = bps_cpe(r, "16QAM", n_angles=48, window=25)
    assert residual_phase_variance(comp[50:-50], s[50:-50]) < 5e-3


def test_gardner_scurve_zero_at_correct_timing():
    """Gardner TED ~0 at aligned timing and changes sign across it (S-curve)."""
    rng = np.random.default_rng(5)
    sps = 4
    c = get_constellation("QPSK")
    s = modulate(rng.integers(0, 2, 3000 * 2), c)
    # upsample with a raised-cosine-ish interpolation via zero-insert + smoothing
    up = np.zeros(len(s) * sps, dtype=complex); up[::sps] = s
    h = np.hanning(2 * sps + 1); h /= h.sum()
    wf = np.convolve(up, h, mode="same")
    # aligned: TED near zero; shifted by +/- : opposite signs
    e0 = gardner_ted(wf, sps)
    ep = gardner_ted(np.roll(wf, 1), sps)
    em = gardner_ted(np.roll(wf, -1), sps)
    assert abs(e0) < abs(ep) and abs(e0) < abs(em)
    assert np.sign(ep) != np.sign(em)                        # sign flips across zero


def test_oerder_meyr_recovers_timing_offset():
    rng = np.random.default_rng(6)
    sps = 4
    c = get_constellation("QPSK")
    s = modulate(rng.integers(0, 2, 4000 * 2), c)
    up = np.zeros(len(s) * sps, dtype=complex); up[::sps] = s
    h = np.hanning(2 * sps + 1); h /= h.sum()
    wf = np.convolve(up, h, mode="same")
    base = oerder_meyr_timing(wf, sps)
    shifted = oerder_meyr_timing(np.roll(wf, 1), sps)        # shift by 1 sample = 1/sps symbol
    delta = (shifted - base) % 1.0
    assert delta == pytest.approx(1.0 / sps, abs=0.03)


def test_invalid_inputs_raise():
    with pytest.raises(ValueError):
        laser_phase_noise(10, -1.0, RS, np.random.default_rng(0))
    with pytest.raises(ValueError):
        gardner_ted(np.zeros(10), sps=1)
