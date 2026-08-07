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


def test_cv_excess_noise_is_input_referred():
    """xi_R = n_bar / T_q: input-referred, with homodyne polarization selection."""
    p_tot, d = 1e-3, 50.0
    n_bar = raman_photon_occupation(p_tot, d)
    t = SMF28.transmissivity(d)
    assert cv_raman_excess_noise(p_tot, d) == pytest.approx(n_bar / t)


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
    d = 50.0  # inside the calibrated secure window
    rates = [coexistence_cv_key_rate(d, p, 20) for p in (-20, -16, -13)]
    assert all(rates[i] >= rates[i + 1] for i in range(len(rates) - 1))
    assert coexistence_cv_key_rate(d, 5.0, 40) == 0.0


def test_cv_more_restrictive_than_dv_at_long_reach():
    """At high loss the input-referred CV excess noise (xi_R = n_bar/T_q) is
    amplified by 1/T_q, so CV tolerates less classical launch than DV. This is
    the corrected DV/CV ordering: the CV secure boundary sits *below* DV's."""
    from iq4comm.qkd import coexistence_dv_key_rate
    from iq4comm.qkd.raman_spectrum import band_raman_coefficient
    d, nch, r_min = 80.0, 8, 1e-6
    raman = RamanModel(
        raman_coeff_per_km_per_nm=band_raman_coefficient(1546.12, 1550.0),
        quantum_wavelength_nm=1550.0)
    # Extend beyond both corrected security ceilings; a shorter historical
    # sweep clipped the DV result at its upper grid edge.
    grid = np.linspace(-40.0, 16.0, 1121)

    def boundary(fn):
        vals = np.array([fn(d, p, nch, raman=raman) for p in grid])
        ok = vals >= r_min
        return grid[ok][-1] if ok.any() else np.nan

    p_dv = boundary(coexistence_dv_key_rate)
    p_cv = boundary(coexistence_cv_key_rate)
    assert p_cv < p_dv                       # CV is the more restrictive protocol
    assert p_dv == pytest.approx(14.25, abs=0.1)
    assert p_cv == pytest.approx(5.95, abs=0.1)
