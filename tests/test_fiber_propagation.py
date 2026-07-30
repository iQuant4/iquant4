"""Scientific validation of the split-step Fourier fiber engine.

Each test checks the propagator against a closed-form or conserved-quantity
reference, so a passing suite is evidence the physics is right, not merely that
the code runs.
"""

from __future__ import annotations

import numpy as np
import pytest

from iqcore.fiber import (
    TimeGrid,
    gaussian_pulse,
    soliton_pulse,
    propagate,
    FiberSpec,
    SMF28,
)


def _rms_width_ps(field: np.ndarray, grid: TimeGrid) -> float:
    """Intensity-weighted RMS temporal width of a pulse."""
    t = grid.time_ps
    power = np.abs(field) ** 2
    norm = np.sum(power)
    mean = np.sum(t * power) / norm
    var = np.sum((t - mean) ** 2 * power) / norm
    return float(np.sqrt(var))


def test_pure_loss_matches_transmissivity():
    """With dispersion and nonlinearity off, energy decays by exactly eta."""
    grid = TimeGrid(num_points=2048, dt_ps=1.0)
    pulse = gaussian_pulse(grid, peak_power_w=1e-3, width_ps=20.0)
    length = 80.0
    res = propagate(pulse, grid, SMF28, length,
                    include_dispersion=False, include_nonlinearity=False)
    expected_ratio = SMF28.transmissivity(length)
    measured_ratio = res.output_energy_pj / res.input_energy_pj
    assert measured_ratio == pytest.approx(expected_ratio, rel=1e-9)
    # And the reported loss equals alpha * L.
    assert res.loss_db == pytest.approx(SMF28.loss_db(length), rel=1e-9)


def test_dispersion_broadens_gaussian_analytically():
    """A chirp-free Gaussian broadens by sqrt(1 + (L/L_D)^2) under pure GVD."""
    fiber = FiberSpec(attenuation_db_per_km=0.0, dispersion_ps_nm_km=17.0,
                      dispersion_slope_ps_nm2_km=0.0, gamma_per_w_per_km=0.0,
                      name="test-GVD")
    grid = TimeGrid(num_points=8192, dt_ps=0.2)
    t0 = 10.0  # 1/e field half-width in ps
    pulse = gaussian_pulse(grid, peak_power_w=1e-3, width_ps=t0)
    length = 50.0
    res = propagate(pulse, grid, fiber, length,
                    include_loss=False, include_nonlinearity=False)

    l_d = fiber.dispersion_length_km(t0)
    broadening = np.sqrt(1.0 + (length / l_d) ** 2)

    rms_in = _rms_width_ps(pulse, grid)
    rms_out = _rms_width_ps(res.field, grid)
    assert rms_out / rms_in == pytest.approx(broadening, rel=1e-3)


def test_energy_conserved_under_pure_spm():
    """Self-phase modulation is unitary: with loss off, energy is conserved."""
    fiber = FiberSpec(attenuation_db_per_km=0.0, dispersion_ps_nm_km=0.0,
                      dispersion_slope_ps_nm2_km=0.0, gamma_per_w_per_km=1.3,
                      name="test-SPM")
    grid = TimeGrid(num_points=4096, dt_ps=0.5)
    pulse = gaussian_pulse(grid, peak_power_w=0.5, width_ps=10.0)
    res = propagate(pulse, grid, fiber, 40.0, include_loss=False,
                    include_dispersion=False)
    assert res.output_energy_pj == pytest.approx(res.input_energy_pj, rel=1e-10)


def test_pure_spm_peak_nonlinear_phase():
    """Peak SPM phase equals gamma * P0 * L_eff (here L_eff = L, lossless)."""
    fiber = FiberSpec(attenuation_db_per_km=0.0, dispersion_ps_nm_km=0.0,
                      dispersion_slope_ps_nm2_km=0.0, gamma_per_w_per_km=1.3,
                      name="test-SPM")
    grid = TimeGrid(num_points=4096, dt_ps=0.5)
    p0 = 0.5
    length = 30.0
    pulse = gaussian_pulse(grid, peak_power_w=p0, width_ps=12.0)
    res = propagate(pulse, grid, fiber, length, include_loss=False,
                    include_dispersion=False)
    # Nonlinear phase = arg(A_out) - arg(A_in) at the peak (t = 0).
    peak = grid.num_points // 2
    phase = np.angle(res.field[peak] / pulse[peak])
    expected = fiber.gamma_per_w_per_km * p0 * length
    # Compare modulo 2*pi.
    assert np.exp(1j * phase) == pytest.approx(np.exp(1j * expected), abs=1e-3)


def test_fundamental_soliton_preserves_shape():
    """An N=1 soliton keeps its intensity profile over a soliton period."""
    fiber = FiberSpec(attenuation_db_per_km=0.0, dispersion_ps_nm_km=17.0,
                      dispersion_slope_ps_nm2_km=0.0, gamma_per_w_per_km=1.3,
                      name="test-soliton")
    grid = TimeGrid(num_points=8192, dt_ps=0.1)
    t0 = 5.0
    pulse = soliton_pulse(grid, fiber, width_ps=t0, order=1)
    l_d = fiber.dispersion_length_km(t0)
    soliton_period = 0.5 * np.pi * l_d  # z0 = (pi/2) L_D
    res = propagate(pulse, grid, fiber, soliton_period, include_loss=False)

    p_in = np.abs(pulse) ** 2
    p_out = np.abs(res.field) ** 2
    # Shapes should match closely (soliton is shape-invariant).
    corr = np.sum(p_in * p_out) / np.sqrt(np.sum(p_in ** 2) * np.sum(p_out ** 2))
    assert corr == pytest.approx(1.0, abs=2e-3)
    assert np.max(p_out) == pytest.approx(np.max(p_in), rel=2e-2)


def test_zero_length_is_identity():
    grid = TimeGrid(num_points=1024, dt_ps=1.0)
    pulse = gaussian_pulse(grid, peak_power_w=1e-3, width_ps=15.0)
    res = propagate(pulse, grid, SMF28, 0.0)
    assert np.allclose(res.field, pulse)
    assert res.num_steps == 0


def test_transmissivity_bounds_and_effective_length():
    assert SMF28.transmissivity(0.0) == pytest.approx(1.0)
    assert 0.0 < SMF28.transmissivity(100.0) < 1.0
    # Effective length -> length as loss -> 0.
    lossless = FiberSpec(attenuation_db_per_km=0.0, name="lossless")
    assert lossless.effective_length_km(50.0) == pytest.approx(50.0)
    # And saturates below 1/alpha for a long lossy span.
    assert SMF28.effective_length_km(1e6) == pytest.approx(
        1.0 / SMF28.alpha_neper_per_km, rel=1e-6)
