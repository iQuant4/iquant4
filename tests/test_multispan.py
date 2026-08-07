"""Tests for the multi-span coexistence model (amplified classical, un-amplified quantum)."""

from __future__ import annotations

import dataclasses

import numpy as np
import pytest

from iqcore.fiber import SMF28
from iq4comm.qkd.coexistence import (
    coexistence_dv_key_rate, classical_capacity_bps, raman_background_yield,
    RamanModel,
)
from iq4comm.qkd.multispan import (
    multispan_classical_capacity_bps,
    multispan_raman_background_yield,
    multispan_dv_key_rate,
    multispan_cv_key_rate,
    _span_accumulation_factor,
)
from iq4comm.qkd.raman_spectrum import band_raman_coefficient


def test_n1_reduces_to_single_span_dv():
    single = coexistence_dv_key_rate(80.0, -15.0, 8)
    multi = multispan_dv_key_rate(-15.0, 8, 80.0, 1)
    assert multi == pytest.approx(single, rel=1e-9)


def test_n1_reduces_to_single_span_capacity():
    single = classical_capacity_bps(-15.0, 8, 80.0)
    multi = multispan_classical_capacity_bps(-15.0, 8, 80.0, 1)
    assert multi == pytest.approx(single, rel=1e-9)


def test_n1_mixed_band_reduces_to_corrected_single_span():
    """One mixed-band span uses the same unequal-loss kernel in both APIs."""
    oband = dataclasses.replace(SMF28, attenuation_db_per_km=0.32)
    raman_o = RamanModel(
        raman_coeff_per_km_per_nm=band_raman_coefficient(1310.0, 1550.0),
        quantum_wavelength_nm=1310.0,
        pump_attenuation_db_per_km=SMF28.attenuation_db_per_km,
    )
    single = coexistence_dv_key_rate(
        80.0, -2.0, 8, fiber=oband, raman=raman_o)
    multi = multispan_dv_key_rate(
        -2.0, 8, 80.0, 1, fiber=oband, raman=raman_o)
    assert multi == pytest.approx(single, rel=1e-12)


def test_multispan_raman_is_single_span_times_quantum_loss_sum():
    """Only post-generation O-band loss appears in the inter-span sum."""
    span_km = 40.0
    n_spans = 4
    launch_dbm = -5.0
    n_channels = 8
    oband = dataclasses.replace(SMF28, attenuation_db_per_km=0.32)
    raman_o = RamanModel(
        raman_coeff_per_km_per_nm=band_raman_coefficient(1310.0, 1550.0),
        quantum_wavelength_nm=1310.0,
        pump_attenuation_db_per_km=SMF28.attenuation_db_per_km,
    )
    total_launch_w = n_channels * 1e-3 * 10.0 ** (launch_dbm / 10.0)
    one_span = raman_background_yield(
        total_launch_w, span_km, fiber=oband, raman=raman_o,
        detector_efficiency=0.5)
    expected = one_span * _span_accumulation_factor(
        oband, span_km, n_spans)
    actual = multispan_raman_background_yield(
        launch_dbm, n_channels, span_km, n_spans, fiber=oband,
        raman=raman_o, detector_efficiency=0.5)
    assert actual == pytest.approx(expected, rel=1e-12)


def test_mixed_band_uses_lower_cband_pump_loss():
    """C-band pump loss must not silently inherit the larger O-band loss."""
    oband = dataclasses.replace(SMF28, attenuation_db_per_km=0.32)
    rho_o = band_raman_coefficient(1310.0, 1550.0)
    equal_loss = RamanModel(
        raman_coeff_per_km_per_nm=rho_o,
        quantum_wavelength_nm=1310.0,
    )
    mixed_loss = dataclasses.replace(
        equal_loss,
        pump_attenuation_db_per_km=SMF28.attenuation_db_per_km,
    )
    equal_bg = multispan_raman_background_yield(
        -5.0, 8, 40.0, 2, fiber=oband, raman=equal_loss)
    mixed_bg = multispan_raman_background_yield(
        -5.0, 8, 40.0, 2, fiber=oband, raman=mixed_loss)
    assert mixed_bg > equal_bg


def test_accumulation_factor_bounds():
    # N=1 -> exactly 1; N spans -> between 1 and N (residual-span attenuation).
    assert _span_accumulation_factor(SMF28, 80.0, 1) == pytest.approx(1.0)
    acc = _span_accumulation_factor(SMF28, 80.0, 4)
    assert 1.0 < acc < 4.0
    with pytest.raises(ValueError, match="n_spans"):
        _span_accumulation_factor(SMF28, 80.0, 0)


def test_quantum_reach_collapses_with_spans():
    # Un-amplifiable O-band quantum channel: key rate falls as spans accumulate.
    oband = dataclasses.replace(SMF28, attenuation_db_per_km=0.32)
    raman_o = RamanModel(
        raman_coeff_per_km_per_nm=band_raman_coefficient(1310.0, 1550.0),
        quantum_wavelength_nm=1310.0,
        pump_attenuation_db_per_km=SMF28.attenuation_db_per_km)
    k1 = multispan_dv_key_rate(-2.0, 8, 80.0, 1, fiber=oband, raman=raman_o)
    k2 = multispan_dv_key_rate(-2.0, 8, 80.0, 2, fiber=oband, raman=raman_o)
    assert k1 > 0.0
    assert k2 < k1                       # more spans -> lower quantum key rate


def test_classical_survives_multiple_spans():
    # Amplified classical link degrades only gradually with span count.
    c1 = multispan_classical_capacity_bps(-2.0, 8, 80.0, 1)
    c4 = multispan_classical_capacity_bps(-2.0, 8, 80.0, 4)
    assert c4 > 0.5 * c1                 # still serviceable at 4 spans


def test_raman_background_grows_with_spans():
    b1 = multispan_raman_background_yield(-10.0, 8, 80.0, 1)
    b3 = multispan_raman_background_yield(-10.0, 8, 80.0, 3)
    assert b3 > b1


def test_cv_multispan_nonnegative():
    k = multispan_cv_key_rate(-15.0, 8, 80.0, 1)
    assert k >= 0.0
