"""Validation of the NLSE solver and digital backpropagation.

Physics references:
* self-phase modulation imprints peak nonlinear phase ``gamma * P0 * L``;
* a fundamental soliton keeps its shape (lossless);
* backpropagation inverts propagation (round-trip identity);
* full DBP beats linear dispersion-only equalisation in a nonlinear regime.
"""

from __future__ import annotations

import numpy as np
import pytest

from iqcore.fiber import (
    TimeGrid,
    gaussian_pulse,
    soliton_pulse,
    propagate,
    backpropagate,
    compensate_dispersion,
    nmse,
    FiberSpec,
    SMF28,
)


def test_spm_peak_phase_matches_gamma_p_l():
    """Pure SPM (no loss/dispersion): peak nonlinear phase = gamma*P0*L, |A| unchanged."""
    grid = TimeGrid(2048, 1.0)
    p0 = 5e-3
    pulse = gaussian_pulse(grid, peak_power_w=p0, width_ps=30.0)
    length = 50.0
    res = propagate(pulse, grid, SMF28, length, include_loss=False,
                    include_dispersion=False, include_nonlinearity=True)
    # Power profile is preserved under pure SPM.
    assert np.allclose(np.abs(res.field), np.abs(pulse), atol=1e-9)
    # Peak nonlinear phase, measured at the peak-power sample (phase 0 on input).
    peak = int(np.argmax(np.abs(pulse)))
    phase = np.angle(res.field[peak]) - np.angle(pulse[peak])
    expected = SMF28.gamma_per_w_per_km * p0 * length
    assert phase == pytest.approx(expected, rel=1e-3)


def test_pure_dispersion_broadening_closed_form():
    """Unchirped Gaussian under pure dispersion broadens by the analytic factor."""
    grid = TimeGrid(4096, 0.5)
    t0 = 10.0
    pulse = gaussian_pulse(grid, peak_power_w=1e-3, width_ps=t0)
    length = 40.0
    res = propagate(pulse, grid, SMF28, length, include_loss=False,
                    include_dispersion=True, include_nonlinearity=False)
    b2 = SMF28.beta2_ps2_per_km()
    ld = t0 ** 2 / abs(b2)
    broaden = np.sqrt(1.0 + (length / ld) ** 2)
    # RMS width ratio (intensity-weighted).
    def rms(field):
        p = np.abs(field) ** 2
        t = grid.time_ps
        mean = np.sum(t * p) / np.sum(p)
        return np.sqrt(np.sum((t - mean) ** 2 * p) / np.sum(p))
    assert rms(res.field) / rms(pulse) == pytest.approx(broaden, rel=1e-2)


def test_fundamental_soliton_preserves_shape():
    """A lossless N=1 soliton keeps its peak power over a soliton period."""
    grid = TimeGrid(4096, 0.5)
    t0 = 8.0
    lossless = FiberSpec(attenuation_db_per_km=0.0, dispersion_ps_nm_km=17.0,
                         gamma_per_w_per_km=1.3, name="lossless-SMF")
    pulse = soliton_pulse(grid, lossless, width_ps=t0, order=1)
    z_soliton = (np.pi / 2.0) * t0 ** 2 / abs(lossless.beta2_ps2_per_km())
    res = propagate(pulse, grid, lossless, z_soliton, include_loss=False)
    # A soliton accumulates a global phase but preserves its intensity profile,
    # so compare magnitude (shape), not the complex field.
    mag_in = np.abs(pulse)
    mag_out = np.abs(res.field)
    assert nmse(mag_out / mag_out.max(), mag_in / mag_in.max()) < 5e-3
    assert mag_out.max() ** 2 == pytest.approx(mag_in.max() ** 2, rel=5e-3)


def test_dbp_round_trip_recovers_launch_field():
    """propagate then backpropagate returns the launched field."""
    grid = TimeGrid(4096, 0.5)
    pulse = gaussian_pulse(grid, peak_power_w=20e-3, width_ps=12.0)
    length = 80.0
    fwd = propagate(pulse, grid, SMF28, length)
    rec = backpropagate(fwd.field, grid, SMF28, length)
    assert nmse(rec.field, pulse) < 1e-3


def test_dbp_beats_linear_equalisation():
    """In a nonlinear regime, full DBP recovers the field better than CD-only."""
    grid = TimeGrid(4096, 0.5)
    pulse = gaussian_pulse(grid, peak_power_w=80e-3, width_ps=10.0)  # high power
    length = 80.0
    fwd = propagate(pulse, grid, SMF28, length)
    # Linear equaliser must also undo the loss (scale) to be comparable.
    scale = np.sqrt(SMF28.transmissivity(length))
    cd_only = compensate_dispersion(fwd.field, grid, SMF28, length) / scale
    dbp = backpropagate(fwd.field, grid, SMF28, length).field
    assert nmse(dbp, pulse) < nmse(cd_only, pulse)
    assert nmse(dbp, pulse) < 1e-3


def test_compensate_dispersion_inverts_pure_dispersion():
    """CD equalisation exactly inverts pure-dispersion propagation."""
    grid = TimeGrid(4096, 0.5)
    pulse = gaussian_pulse(grid, peak_power_w=1e-3, width_ps=8.0)
    length = 60.0
    disp = propagate(pulse, grid, SMF28, length, include_loss=False,
                     include_nonlinearity=False)
    rec = compensate_dispersion(disp.field, grid, SMF28, length)
    assert nmse(rec, pulse) < 1e-9
