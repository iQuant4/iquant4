"""Validation of CV-QKD classical coexistence and the DV/CV consistency link."""

from __future__ import annotations

import numpy as np
import pytest

from iqcore.fiber import SMF28
from iq4comm.qkd import (
    raman_photon_occupation,
    raman_background_yield,
    cv_raman_excess_noise,
    coexistence_cv_key_rate,
    cvqkd_homodyne_key_rate,
    RamanModel,
)


def test_cv_excess_noise_scales_and_zero():
    b1 = cv_raman_excess_noise(1e-3, 50.0)
    b2 = cv_raman_excess_noise(2e-3, 50.0)
    assert b2 == pytest.approx(2 * b1)          # linear in classical power
    assert cv_raman_excess_noise(0.0, 50.0) == 0.0


def test_dv_background_is_occupation_times_modes():
    """DV background = n_bar * (B_filter * t_gate) * eta -- the shared-mode link."""
    raman = RamanModel()
    p_tot = 1e-3
    n_bar = raman_photon_occupation(p_tot, 50.0, raman=raman)
    lam_m = raman.quantum_wavelength_nm * 1e-9
    b_filter_hz = (2.99792458e8 / lam_m ** 2) * (raman.filter_bandwidth_nm * 1e-9)
    modes = b_filter_hz * raman.gate_time_s
    expected = n_bar * modes * 0.5   # detector efficiency
    assert raman_background_yield(p_tot, 50.0, detector_efficiency=0.5) == pytest.approx(expected, rel=1e-9)


def test_zero_power_recovers_isolated_cv():
    d = 50.0
    coex = coexistence_cv_key_rate(d, -np.inf, 20)
    iso = cvqkd_homodyne_key_rate(SMF28.transmissivity(d), excess_noise=0.01)
    assert coex == pytest.approx(iso)


def test_more_classical_power_lowers_cv_rate():
    d = 50.0
    rates = [coexistence_cv_key_rate(d, p, 20) for p in (-12, -8, -6)]
    assert all(rates[i] >= rates[i + 1] for i in range(len(rates) - 1))
    assert coexistence_cv_key_rate(d, 5.0, 40) == 0.0


def test_cv_delivers_higher_rate_than_dv_when_both_secure():
    """Where both protocols close a key, CV yields the higher rate here."""
    from iq4comm.qkd import coexistence_dv_key_rate
    d = 50.0
    for p in (-15, -10, -8):
        cv = coexistence_cv_key_rate(d, p, 20)
        dv = coexistence_dv_key_rate(d, p, 20)
        assert cv > 0 and dv > 0 and cv > dv
