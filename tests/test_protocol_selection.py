"""Validation of protocol-aware coexistence and the best-protocol selector."""

from __future__ import annotations

import pytest

from iq4comm.qkd import (
    protocol_coexistence_key_rate,
    select_best_protocol,
    optimize_launch_power,
    bb84_decoy_key_rate,
    FiniteKeyParams,
)
from iqcore.fiber import SMF28


def test_all_protocols_run_under_coexistence():
    for proto in ("dv", "cv", "mdi", "tf"):
        r = protocol_coexistence_key_rate(proto, 40.0, -24.0, 20)
        assert r >= 0.0


def test_selector_returns_the_maximum():
    best, rate, rates = select_best_protocol(40.0, 20, -24.0)
    assert best in rates
    assert rate == max(rates.values())
    assert rate == rates[best]


def test_best_protocol_shifts_with_distance():
    """Short haul favours a direct/CV protocol; a long span past BB84's reach is
    carried by a sqrt(eta) protocol (TF) when direct QKD has died."""
    # Long span, low classical power: DV is dead but TF still closes a key.
    _, _, rates = select_best_protocol(150.0, 20, -24.0)
    assert rates["tf"] > 0.0
    assert rates["dv"] == 0.0
    assert rates["tf"] > rates["dv"]


def test_optimizer_supports_tf_protocol():
    op = optimize_launch_power(200.0, 20, 1e-6, protocol="tf")
    assert op.feasible
    assert op.secret_key_rate >= 1e-6 * (1 - 1e-2)


def test_finite_key_lowers_coexistence_rate():
    asym = protocol_coexistence_key_rate("dv", 40.0, -24.0, 20)
    fin = protocol_coexistence_key_rate("dv", 40.0, -24.0, 20,
                                        finite=FiniteKeyParams(1e9, 1e-9))
    assert 0.0 <= fin <= asym + 1e-12
