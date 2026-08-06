"""Tests for the wavelength-resolved spontaneous-Raman coexistence profile."""

from __future__ import annotations

import numpy as np
import pytest

from iq4comm.qkd.raman_spectrum import (
    silica_raman_gain,
    phonon_occupation,
    spontaneous_raman_efficiency,
    band_raman_coefficient,
    resolved_raman_rho_effective,
    ClassicalChannel,
    ANCHOR_RHO_PER_KM_PER_NM,
)


def test_silica_gain_peaks_near_13thz():
    f = np.linspace(1e12, 40e12, 4000)
    g = np.array([silica_raman_gain(x) for x in f])
    peak_thz = f[int(np.argmax(g))] / 1e12
    assert peak_thz == pytest.approx(13.2, abs=0.6)   # silica Raman peak
    assert silica_raman_gain(0.0) == pytest.approx(0.0, abs=1e-9)
    assert g.max() == pytest.approx(1.0, rel=1e-6)     # normalised to unit peak


def test_gain_symmetric_in_offset_sign():
    assert silica_raman_gain(5e12) == pytest.approx(silica_raman_gain(-5e12))


def test_phonon_occupation_limits():
    # Large offset -> negligible thermal population; small offset -> large.
    assert phonon_occupation(35e12) < 1e-2
    assert phonon_occupation(0.3e12) > 3.0
    # Monotonically decreasing in offset.
    assert phonon_occupation(1e12) > phonon_occupation(10e12)


def test_stokes_exceeds_antistokes():
    # Positive offset (Stokes) carries n+1; negative (anti-Stokes) carries n.
    dnu = 8e12
    assert spontaneous_raman_efficiency(dnu) > spontaneous_raman_efficiency(-dnu)


def test_anchor_reproduces_scalar_calibration():
    # In-band C-band pair reproduces the calibrated scalar coefficient.
    rho = band_raman_coefficient(1546.12, 1549.0)
    assert rho == pytest.approx(ANCHOR_RHO_PER_KM_PER_NM, rel=0.2)


def test_oband_strongly_suppressed():
    # O-band quantum (1310) with C-band classical (1550): anti-Stokes, ~35 THz.
    rho_c = band_raman_coefficient(1546.12, 1549.0)
    rho_o = band_raman_coefficient(1310.0, 1550.0)
    ratio_db = 10 * np.log10(rho_c / rho_o)
    assert 25.0 < ratio_db < 40.0        # 2-3 decades, matches literature band


def test_resolved_vector_reduces_to_single_channel():
    q = 1546.12
    one = band_raman_coefficient(q, 1549.0)
    vec = resolved_raman_rho_effective(q, [ClassicalChannel(1549.0, 1e-3)])
    assert vec == pytest.approx(one)


def test_resolved_vector_is_power_weighted_mean():
    q = 1546.12
    chans = [ClassicalChannel(1549.0, 1e-3), ClassicalChannel(1552.0, 3e-3)]
    eff = resolved_raman_rho_effective(q, chans)
    r1 = band_raman_coefficient(q, 1549.0)
    r2 = band_raman_coefficient(q, 1552.0)
    expected = (r1 * 1e-3 + r2 * 3e-3) / 4e-3
    assert eff == pytest.approx(expected)
    assert resolved_raman_rho_effective(q, []) == 0.0
