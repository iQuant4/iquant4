"""Validation of the QKD-classical DWDM coexistence model."""

from __future__ import annotations

import numpy as np
import pytest

from iqcore.fiber import SMF28
from iq4comm.qkd import (
    RamanModel,
    raman_path_integral_km,
    raman_background_yield,
    coexistence_dv_key_rate,
    classical_capacity_bps,
    coexistence_curve,
    bb84_decoy_key_rate,
)


_DB_TO_NEPER = np.log(10.0) / 10.0


@pytest.mark.parametrize("direction", ["co", "counter"])
def test_raman_path_integral_matches_direct_quadrature(direction):
    """Closed forms reproduce the underlying unequal-loss z integral."""
    length = 73.0
    pump_db_per_km = 0.19
    quantum_db_per_km = 0.32
    alpha_p = pump_db_per_km * _DB_TO_NEPER
    alpha_q = quantum_db_per_km * _DB_TO_NEPER
    z = np.linspace(0.0, length, 50_001)
    if direction == "co":
        integrand = np.exp(-alpha_p * z) * np.exp(-alpha_q * (length - z))
    else:
        integrand = np.exp(-(alpha_p + alpha_q) * (length - z))
    numerical = np.trapezoid(integrand, z)

    closed_form = raman_path_integral_km(
        length,
        pump_attenuation_db_per_km=pump_db_per_km,
        quantum_attenuation_db_per_km=quantum_db_per_km,
        propagation_direction=direction,
    )
    assert closed_form == pytest.approx(numerical, rel=5e-9)


def test_raman_path_integral_equal_loss_limits():
    """The removable singularities reduce to the published equal-loss forms."""
    length = 60.0
    loss_db_per_km = 0.2
    alpha = loss_db_per_km * _DB_TO_NEPER
    co = raman_path_integral_km(
        length,
        pump_attenuation_db_per_km=loss_db_per_km,
        quantum_attenuation_db_per_km=loss_db_per_km,
        propagation_direction="co",
    )
    counter = raman_path_integral_km(
        length,
        pump_attenuation_db_per_km=loss_db_per_km,
        quantum_attenuation_db_per_km=loss_db_per_km,
        propagation_direction="counter",
    )
    assert co == pytest.approx(length * np.exp(-alpha * length), rel=1e-12)
    assert counter == pytest.approx(
        -np.expm1(-2.0 * alpha * length) / (2.0 * alpha), rel=1e-12)


def test_raman_path_integral_is_stable_near_equal_loss():
    equal = raman_path_integral_km(
        100.0,
        pump_attenuation_db_per_km=0.2,
        quantum_attenuation_db_per_km=0.2,
    )
    near_equal = raman_path_integral_km(
        100.0,
        pump_attenuation_db_per_km=0.2 + 1e-10,
        quantum_attenuation_db_per_km=0.2,
    )
    assert near_equal == pytest.approx(equal, rel=1e-8)


def test_counter_propagation_collects_more_long_link_raman():
    """At long equal-loss spans, counter noise saturates while co noise falls."""
    co = RamanModel(propagation_direction="co")
    counter = RamanModel(propagation_direction="counter")
    assert raman_background_yield(1e-3, 80.0, raman=counter) > (
        raman_background_yield(1e-3, 80.0, raman=co)
    )


def test_default_reproduces_digitized_config_g_60km_anchor():
    """The default preserves the paper's x10^-4 axis at the fitted loss."""
    wavelength_nm = 1546.12
    bandwidth_nm = (
        (wavelength_nm * 1e-9) ** 2 / 2.99792458e8 * 10e9 * 1e9
    )
    raman = RamanModel(
        filter_bandwidth_nm=bandwidth_nm,
        gate_time_s=2.5e-9,
        quantum_wavelength_nm=wavelength_nm,
        pump_attenuation_db_per_km=0.3001634467637991,
    )
    fiber = type(SMF28)(
        attenuation_db_per_km=0.3001634467637991,
        dispersion_ps_nm_km=SMF28.dispersion_ps_nm_km,
        dispersion_slope_ps_nm2_km=SMF28.dispersion_slope_ps_nm2_km,
        gamma_per_w_per_km=SMF28.gamma_per_w_per_km,
        reference_wavelength_nm=wavelength_nm,
        core_area_um2=SMF28.core_area_um2,
        name="da-Silva-fit",
    )
    total_launch_w = 14 * 1e-3 * 10.0 ** (-10.5 / 10.0)
    measured_anchor = raman_background_yield(
        total_launch_w, 60.0, fiber=fiber, raman=raman,
        detector_efficiency=0.15)
    assert measured_anchor == pytest.approx(1.20e-4, rel=0.09)


def test_raman_direction_and_loss_validation():
    with pytest.raises(ValueError, match="propagation_direction"):
        RamanModel(propagation_direction="sideways")  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="pump_attenuation"):
        RamanModel(pump_attenuation_db_per_km=-0.2)
    with pytest.raises(ValueError, match="distance_km"):
        raman_path_integral_km(
            -1.0,
            pump_attenuation_db_per_km=0.2,
            quantum_attenuation_db_per_km=0.2,
        )


def test_raman_background_scales_with_power():
    d = 50.0
    b1 = raman_background_yield(1e-3, d)
    b2 = raman_background_yield(2e-3, d)
    assert b2 == pytest.approx(2 * b1)          # linear in classical power
    assert raman_background_yield(0.0, d) == 0.0


def test_zero_classical_power_recovers_isolated_qkd():
    d = 50.0
    coex = coexistence_dv_key_rate(d, -np.inf, 20)  # -inf dBm -> 0 W
    iso = bb84_decoy_key_rate(SMF28.transmissivity(d))
    assert coex == pytest.approx(iso)


def test_more_classical_power_lowers_key_rate():
    d = 100.0
    rates = [coexistence_dv_key_rate(d, p, 20) for p in (-20, -10, 0)]
    # Non-increasing as classical power rises.
    assert all(rates[i] >= rates[i + 1] for i in range(len(rates) - 1))
    # High enough classical power extinguishes the key.
    assert coexistence_dv_key_rate(d, 10.0, 20) == 0.0


def test_more_channels_lowers_key_rate():
    d = 50.0  # -16 dBm: both channel counts still secure, more channels -> lower
    assert coexistence_dv_key_rate(d, -16.0, 40) < coexistence_dv_key_rate(d, -16.0, 10)


def test_classical_capacity_positive_with_interior_gn_optimum():
    grid = np.arange(-25.0, 12.0, 1.0)
    caps = np.array([classical_capacity_bps(p, 20, 50.0) for p in grid])
    assert np.all(caps > 0)
    # A Gaussian-noise optimum: the peak is interior, not at either extreme.
    peak = int(np.argmax(caps))
    assert 0 < peak < len(caps) - 1


def test_secure_window_and_tradeoff():
    """A secure launch-power window exists; past it, the key dies but classical
    capacity remains -- the coexistence tradeoff."""
    grid = np.arange(-20, 15, 1.0)
    pts = coexistence_curve(100.0, 20, grid)
    secure = [p for p in pts if p.secure and p.classical_capacity_bps > 0]
    assert len(secure) > 0
    # Key rate is non-increasing in launch power.
    skr = [p.secret_key_rate for p in pts]
    assert all(skr[i] >= skr[i + 1] for i in range(len(skr) - 1))
    # At the highest power the key is dead but classical capacity is still large.
    assert pts[-1].secret_key_rate == 0.0
    assert pts[-1].classical_capacity_bps > 5e11
