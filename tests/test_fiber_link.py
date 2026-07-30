"""Validation of the amplifier and multi-span link models.

Checks are against analytical references: amplifier gain and ASE power, the
textbook N-span OSNR formula (including its 3 dB-per-doubling penalty), and
loss-compensated signal recovery.
"""

from __future__ import annotations

import numpy as np
import pytest

from iqcore.fiber import (
    TimeGrid,
    gaussian_pulse,
    Amplifier,
    Link,
    SMF28,
)
from iqcore.fiber.amplifier import PLANCK_J_S, SPEED_OF_LIGHT_M_PER_S


def _pulse_energy(field, grid):
    return float(np.sum(np.abs(field) ** 2) * grid.dt_ps)


def test_amplifier_gain_no_ase():
    """With ASE off, output power is exactly G * input power."""
    grid = TimeGrid(2048, 0.5)
    pulse = gaussian_pulse(grid, peak_power_w=1e-3, width_ps=15.0)
    amp = Amplifier(gain_db=16.0, noise_figure_db=5.0)
    out = amp.amplify(pulse, grid, add_ase=False)
    ratio = _pulse_energy(out, grid) / _pulse_energy(pulse, grid)
    assert ratio == pytest.approx(amp.gain_linear, rel=1e-12)


def test_amplifier_ase_power_matches_psd():
    """Mean ASE power (ASE only) matches S_ASE * B_sim to within sampling error."""
    grid = TimeGrid(1 << 16, 0.5)  # many samples for a stable mean
    zero = np.zeros(grid.num_points, dtype=np.complex128)
    amp = Amplifier(gain_db=20.0, noise_figure_db=5.0)
    rng = np.random.default_rng(12345)
    noise = amp.amplify(zero, grid, add_ase=True, rng=rng, polarizations=1)
    measured = float(np.mean(np.abs(noise) ** 2))
    bandwidth = 1.0 / (grid.dt_ps * 1e-12)
    expected = amp.ase_psd_w_per_hz(polarizations=1) * bandwidth
    assert measured == pytest.approx(expected, rel=0.05)


def test_link_net_gain_and_passive_transmissivity():
    """A span exactly compensated by an amplifier has ~0 dB net gain."""
    link = Link().span(SMF28, 80.0).amplifier(
        Amplifier(gain_db=SMF28.loss_db(80.0), noise_figure_db=5.0))
    assert link.net_gain_db == pytest.approx(0.0, abs=1e-9)
    # Passive transmissivity ignores amplifiers (quantum-branch view).
    assert link.passive_transmissivity == pytest.approx(
        SMF28.transmissivity(80.0), rel=1e-12)
    assert link.total_length_km == pytest.approx(80.0)


def test_link_osnr_matches_textbook_formula():
    """N identical loss-compensated spans reproduce the closed-form OSNR."""
    span_km = 80.0
    loss_db = SMF28.loss_db(span_km)
    nf_db = 5.0
    launch_w = 1e-3  # 0 dBm
    b_ref = 12.5e9
    nu = SPEED_OF_LIGHT_M_PER_S / 1550e-9
    # -10 log10(h*nu*B) with power in mW.
    noise_ref_const = -10.0 * np.log10(PLANCK_J_S * nu * b_ref * 1e3)
    p_launch_dbm = 10.0 * np.log10(launch_w * 1e3)

    prev = None
    for n_spans in (1, 2, 4, 8):
        link = Link(reference_bandwidth_hz=b_ref)
        for _ in range(n_spans):
            link.span(SMF28, span_km).amplifier(
                Amplifier(gain_db=loss_db, noise_figure_db=nf_db))
        expected = (p_launch_dbm - loss_db - nf_db
                    + noise_ref_const - 10.0 * np.log10(n_spans))
        assert link.osnr_db(launch_w) == pytest.approx(expected, abs=1e-6)
        # 3 dB penalty per doubling of span count.
        if prev is not None:
            assert prev - link.osnr_db(launch_w) == pytest.approx(3.0103, abs=1e-3)
        prev = link.osnr_db(launch_w)


def test_loss_compensated_span_recovers_signal_power():
    """Span + matched amplifier (ASE off) restores the launch power."""
    grid = TimeGrid(4096, 0.5)
    pulse = gaussian_pulse(grid, peak_power_w=1e-3, width_ps=40.0)
    e_in = _pulse_energy(pulse, grid)
    link = Link().span(SMF28, 80.0).amplifier(
        Amplifier(gain_db=SMF28.loss_db(80.0)))
    out = link.propagate_field(pulse, grid, add_ase=False)
    e_out = _pulse_energy(out, grid)
    assert e_out == pytest.approx(e_in, rel=1e-6)


def test_link_repr_and_counts():
    link = Link()
    for _ in range(3):
        link.span(SMF28, 50.0).amplifier(Amplifier(gain_db=10.0))
    assert len(link.spans) == 3
    assert len(link.amplifiers) == 3
    assert "3 spans" in repr(link)
