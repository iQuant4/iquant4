"""Validation of the pulse-shaping filters and their spectral figures of merit."""

from __future__ import annotations

import numpy as np
import pytest

from iq4comm.dsp import (
    PulseShape,
    rrc_impulse_response,
    rc_impulse_response,
    sinc_impulse_response,
    impulse_response,
    occupied_bandwidth_hz,
    nyquist_channel_spacing_hz,
    spectral_efficiency_bits_per_hz,
    residual_isi,
    PULSE_SHAPES,
)


def test_rc_is_nyquist_zero_isi():
    """The raised-cosine pulse is ~0 at every nonzero integer symbol instant."""
    sps = 16
    t, h = rc_impulse_response(0.25, span_symbols=12, sps=sps)
    for k in range(1, 12):
        idx = np.argmin(np.abs(t - k))
        assert abs(h[idx]) < 1e-9


def test_sinc_is_zero_isi_and_narrowest():
    t, h = sinc_impulse_response(span_symbols=12, sps=16)
    for k in range(1, 12):
        idx = np.argmin(np.abs(t - k))
        assert abs(h[idx]) < 1e-9
    # Sinc occupies exactly Rs; RC with roll-off occupies more.
    rs = 32e9
    assert occupied_bandwidth_hz("sinc", rs) == pytest.approx(rs)
    assert occupied_bandwidth_hz("rc", rs, beta=0.3) > rs


def test_rrc_matched_pair_is_raised_cosine():
    """rrc (X) rrc == raised-cosine: the cascade is Nyquist (zero ISI)."""
    beta, sps = 0.3, 16
    _t, g = rrc_impulse_response(beta, span_symbols=16, sps=sps)
    casc = np.convolve(g, g)
    casc = casc / casc.max()
    center = len(casc) // 2
    for k in range(1, 10):
        assert abs(casc[center + k * sps]) < 5e-3     # ~zero at symbol instants


def test_occupied_bandwidth_matches_analytic_nyquist():
    """RC / RRC occupy Rs*(1+beta) exactly."""
    rs = 32e9
    for beta in (0.0, 0.1, 0.35, 0.7, 1.0):
        assert occupied_bandwidth_hz("rc", rs, beta=beta) == pytest.approx(rs * (1 + beta))
        assert occupied_bandwidth_hz("rrc", rs, beta=beta) == pytest.approx(rs * (1 + beta))


def test_spectral_efficiency_is_k_over_one_plus_beta():
    """Spectral efficiency of a Nyquist shape is k/(1+beta)."""
    rs = 32e9
    for k, beta in ((2, 0.2), (4, 0.1), (6, 0.5)):
        se = spectral_efficiency_bits_per_hz("rrc", k, beta=beta, symbol_rate_baud=rs)
        assert se == pytest.approx(k / (1 + beta))


def test_lower_rolloff_packs_tighter_and_more_efficient():
    rs = 32e9
    s_sharp = nyquist_channel_spacing_hz("rrc", rs, beta=0.05)
    s_soft = nyquist_channel_spacing_hz("rrc", rs, beta=0.5)
    assert s_sharp < s_soft                            # tighter grid
    se_sharp = spectral_efficiency_bits_per_hz("rrc", 4, beta=0.05, symbol_rate_baud=rs)
    se_soft = spectral_efficiency_bits_per_hz("rrc", 4, beta=0.5, symbol_rate_baud=rs)
    assert se_sharp > se_soft


def test_guard_band_widens_spacing():
    rs = 32e9
    base = nyquist_channel_spacing_hz("rrc", rs, beta=0.2, guard_fraction=0.0)
    guarded = nyquist_channel_spacing_hz("rrc", rs, beta=0.2, guard_fraction=0.1)
    assert guarded == pytest.approx(1.1 * base)


def test_rect_is_spectrally_wider_than_nyquist():
    """A rectangular NRZ pulse occupies more 99%-power bandwidth than a sinc."""
    rs = 32e9
    bw_rect = occupied_bandwidth_hz("rect", rs)
    assert bw_rect > rs                                # side-lobes spill energy


def test_nyquist_shapes_have_negligible_residual_isi():
    assert residual_isi("rrc", beta=0.25) < 5e-3
    assert residual_isi("rc", beta=0.25) < 1e-9
    assert residual_isi("sinc") < 1e-9


def test_gaussian_has_real_isi():
    """A Gaussian pulse is not Nyquist -- it leaves measurable ISI."""
    isi = residual_isi("gaussian", bt=0.3)
    assert isi > 1e-3


def test_pulseshape_object_api():
    ps = PulseShape("rrc", beta=0.15)
    rs = 32e9
    assert ps.occupied_bandwidth_hz(rs) == pytest.approx(rs * 1.15)
    assert ps.spectral_efficiency_bits_per_hz(4, symbol_rate_baud=rs) == pytest.approx(4 / 1.15)
    assert ps.channel_spacing_hz(rs, guard_fraction=0.2) == pytest.approx(rs * 1.15 * 1.2)


def test_invalid_inputs_raise():
    with pytest.raises(ValueError):
        rrc_impulse_response(1.5)                      # beta out of range
    with pytest.raises(ValueError):
        impulse_response("bogus")
    with pytest.raises(ValueError):
        PulseShape("nope")
    with pytest.raises(ValueError):
        occupied_bandwidth_hz("rc", 32e9, beta=-0.1)
