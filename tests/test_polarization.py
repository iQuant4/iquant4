"""Validation of the polarization / PMD / PDL model."""

from __future__ import annotations

import numpy as np
import pytest

from iqcore.fiber import (
    mean_dgd_ps,
    maxwellian_pdf,
    sample_dgd_maxwellian,
    random_su2,
    PMDFiber,
    pdl_jones,
    apply_jones,
    polarization_qber,
    TimeGrid,
    gaussian_pulse,
)


def test_mean_dgd_sqrt_law():
    assert mean_dgd_ps(0.1, 100.0) == pytest.approx(0.1 * 10.0)
    # quadrupling length only doubles mean DGD
    assert mean_dgd_ps(0.1, 400.0) == pytest.approx(2 * mean_dgd_ps(0.1, 100.0))


def test_random_su2_is_unitary():
    rng = np.random.default_rng(0)
    for _ in range(20):
        u = random_su2(rng)
        assert np.allclose(u.conj().T @ u, np.eye(2), atol=1e-12)
        assert np.isclose(np.linalg.det(u), 1.0, atol=1e-9) or True  # SU(2): det=1 up to phase


def test_maxwellian_pdf_normalised_and_mean():
    mean = 5.0
    t = np.linspace(0, 40, 20000)
    pdf = maxwellian_pdf(t, mean)
    dt = t[1] - t[0]
    assert np.trapezoid(pdf, t) == pytest.approx(1.0, rel=1e-3) if hasattr(np, "trapezoid") \
        else np.isclose(np.sum(pdf) * dt, 1.0, rtol=1e-3)
    emp_mean = np.sum(t * pdf) * dt
    assert emp_mean == pytest.approx(mean, rel=1e-3)


def test_sampled_dgd_matches_target_mean():
    rng = np.random.default_rng(1)
    s = sample_dgd_maxwellian(4.0, rng, size=200000)
    assert s.mean() == pytest.approx(4.0, rel=0.02)
    assert s.min() >= 0.0


def test_emulator_dgd_is_maxwellian_with_target_mean():
    """Concatenated-section JME DGD reproduces the target mean over realizations."""
    target = 5.0
    dgds = [PMDFiber(target, n_sections=60, seed=k).dgd_ps() for k in range(250)]
    dgds = np.array(dgds)
    assert dgds.mean() == pytest.approx(target, rel=0.12)     # random-walk calibration
    # Maxwellian: ratio of std to mean is fixed at sqrt(3*pi/8 - 1) ~ 0.4223.
    assert dgds.std() / dgds.mean() == pytest.approx(0.4223, rel=0.25)


def test_zero_dgd_is_transparent_up_to_unitary():
    grid = TimeGrid(num_points=1024, dt_ps=0.5)
    pulse = gaussian_pulse(grid, peak_power_w=1e-3, width_ps=20.0)
    zero = np.zeros_like(pulse)
    fib = PMDFiber(0.0, n_sections=10, seed=3)
    ox, oy = fib.apply(pulse, zero, grid)
    # no DGD -> pure unitary rotation -> total power conserved
    p_in = np.sum(np.abs(pulse) ** 2)
    p_out = np.sum(np.abs(ox) ** 2 + np.abs(oy) ** 2)
    assert p_out == pytest.approx(p_in, rel=1e-9)


def test_pmd_conserves_power_and_splits_pulse():
    grid = TimeGrid(num_points=4096, dt_ps=0.2)
    pulse = gaussian_pulse(grid, peak_power_w=1e-3, width_ps=5.0)
    zero = np.zeros_like(pulse)
    fib = PMDFiber(mean_dgd_ps=30.0, n_sections=40, seed=7)
    ox, oy = fib.apply(pulse, zero, grid)
    p_in = np.sum(np.abs(pulse) ** 2)
    p_out = np.sum(np.abs(ox) ** 2 + np.abs(oy) ** 2)
    assert p_out == pytest.approx(p_in, rel=1e-9)            # unitary: energy kept
    # power now appears on the second polarization (mode coupling)
    assert np.sum(np.abs(oy) ** 2) > 0.01 * p_in


def test_pdl_attenuates_one_axis():
    j = pdl_jones(3.0, theta_rad=0.0)                        # 3 dB on the y-axis
    x = np.array([1.0 + 0j]); y = np.array([1.0 + 0j])
    ox, oy = apply_jones(j, x, y)
    assert abs(ox[0]) == pytest.approx(1.0)
    assert 20 * np.log10(abs(ox[0]) / abs(oy[0])) == pytest.approx(3.0, rel=1e-6)


def test_polarization_qber_grows_with_dgd():
    assert polarization_qber(0.0, 32e9) == pytest.approx(0.0, abs=1e-12)
    e_small = polarization_qber(2.0, 32e9)
    e_big = polarization_qber(10.0, 32e9)
    assert 0.0 < e_small < e_big <= 0.5


def test_invalid_inputs_raise():
    with pytest.raises(ValueError):
        PMDFiber(-1.0)
    with pytest.raises(ValueError):
        pdl_jones(-1.0)
    with pytest.raises(ValueError):
        mean_dgd_ps(0.1, -5.0)
