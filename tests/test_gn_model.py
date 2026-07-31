"""Validation of the GN model against its analytical properties."""

from __future__ import annotations

import numpy as np
import pytest

from iqcore.fiber import Amplifier, SMF28
from iq4comm.dsp import (
    nli_coefficient,
    nli_power_w,
    effective_snr,
    optimal_launch_power_w,
    ase_power_w,
    gn_operating_point,
    ber_theory,
)

RS = 32e9          # 32 GBd
BWDM = 40 * 50e9   # 40 channels x 50 GHz = 2 THz
SPAN = 80.0


def test_nli_scales_as_power_cubed():
    eta = nli_coefficient(SMF28, SPAN, 10, RS, BWDM)
    p = 1e-3
    assert nli_power_w(eta, 2 * p) == pytest.approx(8 * nli_power_w(eta, p))
    assert nli_power_w(eta, 3 * p) == pytest.approx(27 * nli_power_w(eta, p))


def test_nli_accumulates_linearly_with_spans():
    e1 = nli_coefficient(SMF28, SPAN, 1, RS, BWDM)
    e10 = nli_coefficient(SMF28, SPAN, 10, RS, BWDM)
    assert e10 == pytest.approx(10 * e1)


def test_optimal_launch_matches_numerical_and_half_ase_condition():
    eta = nli_coefficient(SMF28, SPAN, 12, RS, BWDM)
    amp = Amplifier(gain_db=SMF28.loss_db(SPAN), noise_figure_db=5.0)
    p_ase = ase_power_w(amp, 12, RS)
    p_opt = optimal_launch_power_w(p_ase, eta)

    # Numerical argmax of SNR over a fine power sweep agrees with closed form.
    powers = np.logspace(np.log10(p_opt) - 1, np.log10(p_opt) + 1, 20001)
    snr = powers / (p_ase + eta * powers ** 3)
    p_num = powers[int(np.argmax(snr))]
    assert p_num == pytest.approx(p_opt, rel=1e-3)

    # At the optimum the NLI is exactly half the ASE.
    assert nli_power_w(eta, p_opt) == pytest.approx(p_ase / 2.0, rel=1e-9)


def test_effective_snr_has_finite_maximum():
    eta = nli_coefficient(SMF28, SPAN, 10, RS, BWDM)
    amp = Amplifier(gain_db=SMF28.loss_db(SPAN), noise_figure_db=5.0)
    p_ase = ase_power_w(amp, 10, RS)
    p_opt = optimal_launch_power_w(p_ase, eta)
    snr_opt = effective_snr(p_opt, p_ase, eta)
    # Moving away from the optimum in either direction lowers the SNR.
    assert effective_snr(p_opt * 0.5, p_ase, eta) < snr_opt
    assert effective_snr(p_opt * 2.0, p_ase, eta) < snr_opt


def test_operating_point_reasonable_and_reach_finite():
    """Optimal launch/SNR are physical, and BER now reaches a finite distance."""
    amp = Amplifier(gain_db=SMF28.loss_db(SPAN), noise_figure_db=5.0)
    op = gn_operating_point(SMF28, SPAN, 12, amp, RS, BWDM)
    # Optimal launch is in a sane per-channel window and SNR is a real number.
    assert -6.0 < op.optimal_launch_dbm < 6.0
    assert 8.0 < op.max_snr_db < 30.0
    assert op.nli_to_ase_ratio == pytest.approx(0.5, rel=1e-9)

    # Effective SNR (dual-pol QPSK: Eb/N0 = SNR/2) gives a finite FEC-limited reach.
    def reach_ok(fmt, k):
        crossed = None
        for n in range(1, 200):
            o = gn_operating_point(SMF28, SPAN, n, amp, RS, BWDM)
            snr_lin = 10 ** (o.max_snr_db / 10.0)
            ebn0_db = 10 * np.log10(snr_lin / k)
            if ber_theory(fmt, ebn0_db) > 3.8e-3:  # 7% FEC threshold
                crossed = (n - 1) * SPAN
                break
        return crossed
    reach_qpsk = reach_ok("QPSK", 2)
    reach_16 = reach_ok("16QAM", 4)
    assert reach_qpsk is not None and reach_16 is not None
    assert reach_qpsk > reach_16 > 0  # denser format -> shorter reach
