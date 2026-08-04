"""Validation of the reach-extension QKD protocols."""

from __future__ import annotations

import numpy as np
import pytest

from iqcore.fiber import SMF28
from iq4comm.qkd import (
    bb84_decoy_key_rate,
    mdi_qkd_key_rate,
    tf_qkd_key_rate,
    trusted_node_key_rate,
    plob_bound_bits,
)


def _slope(fn, eta_lo=1e-5, eta_hi=1e-4):
    """Log-log slope of rate vs transmissivity (loss-dominated regime)."""
    r_lo, r_hi = fn(eta_lo), fn(eta_hi)
    return np.log(r_hi / r_lo) / np.log(eta_hi / eta_lo)


def test_tf_scales_as_sqrt_eta():
    """TF-QKD rate ~ sqrt(eta): log-log slope near 1/2."""
    assert _slope(tf_qkd_key_rate) == pytest.approx(0.5, abs=0.05)


def test_mdi_and_bb84_scale_as_eta():
    """MDI and BB84 rates ~ eta: log-log slope near 1 (sampled where both live)."""
    assert _slope(mdi_qkd_key_rate, 2e-3, 2e-2) == pytest.approx(1.0, abs=0.1)
    assert _slope(bb84_decoy_key_rate, 2e-3, 2e-2) == pytest.approx(1.0, abs=0.1)


def test_tf_beats_plob_at_long_distance():
    """TF-QKD exceeds the repeaterless PLOB bound at long distance."""
    eta = SMF28.transmissivity(300.0)          # ~60 dB
    assert tf_qkd_key_rate(eta) > plob_bound_bits(eta)
    # ...and BB84 never beats PLOB.
    assert bb84_decoy_key_rate(eta) <= plob_bound_bits(eta) + 1e-15


def test_tf_reaches_further_than_bb84():
    d = np.arange(0, 600, 2.0)
    tf = np.array([tf_qkd_key_rate(SMF28.transmissivity(x)) for x in d])
    dv = np.array([bb84_decoy_key_rate(SMF28.transmissivity(x)) for x in d])
    reach_tf = d[np.max(np.where(tf > 0))]
    reach_dv = d[np.max(np.where(dv > 0))]
    assert reach_tf > reach_dv


def test_mdi_below_bb84_same_distance():
    """MDI has a coincidence penalty, so its rate is below BB84 at equal loss."""
    for dkm in (20.0, 60.0, 100.0):
        eta = SMF28.transmissivity(dkm)
        assert mdi_qkd_key_rate(eta) < bb84_decoy_key_rate(eta)


def test_bb84_short_range_beats_tf():
    """At short range BB84 (~eta) out-rates TF (~sqrt(eta) but lower prefactor)."""
    eta = SMF28.transmissivity(10.0)
    assert bb84_decoy_key_rate(eta) > tf_qkd_key_rate(eta)


def test_trusted_nodes_extend_reach():
    """Trusted nodes lift the rate at a distance where direct QKD has died."""
    d = 400.0
    assert trusted_node_key_rate(d, 0) == pytest.approx(
        bb84_decoy_key_rate(SMF28.transmissivity(d)))   # 0 nodes = direct
    assert trusted_node_key_rate(d, 0) == 0.0            # direct BB84 dead at 400 km
    assert trusted_node_key_rate(d, 3) > 0.0             # 4 segments of 100 km: alive
    # More nodes -> shorter segments -> higher rate.
    assert trusted_node_key_rate(d, 7) > trusted_node_key_rate(d, 3)
