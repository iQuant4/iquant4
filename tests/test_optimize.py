"""Validation of the joint coexistence optimizer."""

from __future__ import annotations

import numpy as np
import pytest

from iq4comm.qkd import (
    optimize_launch_power,
    coexistence_reach,
    coexistence_dv_key_rate,
    classical_capacity_bps,
)


def test_optimum_meets_constraint_and_is_secure():
    op = optimize_launch_power(50.0, 20, min_key_rate=1e-4, protocol="dv")
    assert op.feasible
    # Meets the key-rate target (within the boundary-solver tolerance).
    assert op.secret_key_rate >= 1e-4 * (1 - 1e-2)
    # The reported capacity matches an independent evaluation at that launch.
    assert op.classical_capacity_bps == pytest.approx(
        classical_capacity_bps(op.launch_dbm, 20, 50.0), rel=1e-6)


def test_constraint_binds_when_qkd_is_tight():
    """A demanding key-rate target forces backing off below the GN optimum."""
    strict = optimize_launch_power(50.0, 20, min_key_rate=1e-3, protocol="dv")
    assert strict.feasible and strict.qkd_constraint_binds
    # At the optimum the key rate sits essentially at the requirement.
    assert strict.secret_key_rate == pytest.approx(1e-3, rel=5e-3)


def test_loose_constraint_reaches_gn_optimum():
    """When QKD is easy (short reach, few channels) classical runs at its own
    GN optimum and the quantum constraint does not bind."""
    d, nch = 10.0, 4
    loose = optimize_launch_power(d, nch, min_key_rate=1e-9, protocol="dv")
    grid = np.arange(-25, 8, 0.5)
    caps = [classical_capacity_bps(p, nch, d) for p in grid]
    p_gn = grid[int(np.argmax(caps))]
    assert loose.launch_dbm == pytest.approx(p_gn, abs=0.75)
    assert not loose.qkd_constraint_binds


def test_infeasible_when_key_rate_unreachable():
    op = optimize_launch_power(50.0, 20, min_key_rate=1.0, protocol="dv")  # 1 bit/pulse impossible
    assert not op.feasible


def test_cv_optimizer_runs_and_binds_reasonably():
    op = optimize_launch_power(50.0, 20, min_key_rate=1e-3, protocol="cv")
    assert op.feasible
    assert op.secret_key_rate >= 1e-3 - 1e-9


def test_coexistence_reach_monotonic_in_key_rate_target():
    """A stricter key-rate requirement cannot increase the reachable distance."""
    cap_target = 1e12  # 1 Tb/s
    easy = coexistence_reach(20, 1e-4, cap_target, protocol="dv")
    hard = coexistence_reach(20, 1e-3, cap_target, protocol="dv")
    assert easy >= hard > 0
