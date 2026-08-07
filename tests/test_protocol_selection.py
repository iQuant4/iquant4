"""Validation of protocol-aware coexistence and the best-protocol selector."""

from __future__ import annotations

import pytest

from iq4comm.qkd import (
    protocol_coexistence_key_rate,
    select_best_protocol,
    optimize_launch_power,
    bb84_decoy_key_rate,
    FiniteKeyParams,
    ModelStatus,
    ScalingProxyOptInRequired,
)
from iqcore.fiber import SMF28


def test_research_protocols_run_and_proxies_require_opt_in():
    for proto in ("dv", "cv"):
        r = protocol_coexistence_key_rate(proto, 40.0, -24.0, 20)
        assert r >= 0.0
    for proto in ("mdi", "tf"):
        with pytest.raises(ScalingProxyOptInRequired):
            protocol_coexistence_key_rate(proto, 40.0, -24.0, 20)
        r = protocol_coexistence_key_rate(
            proto, 40.0, -24.0, 20, allow_scaling_proxy=True)
        assert r >= 0.0


def test_selector_returns_the_maximum():
    best, rate, rates = select_best_protocol(40.0, 20, -24.0)
    assert set(rates) == {"dv", "cv"}
    assert best in rates
    assert rate == max(rates.values())
    assert rate == rates[best]


def test_selector_reports_but_never_recommends_scaling_proxy():
    """A positive TF proxy is diagnostic only when eligible models have died."""
    best, best_rate, rates = select_best_protocol(
        220.0, 20, -5.0, include_scaling_proxies=True)
    assert rates["tf"] > 0.0
    assert rates["dv"] == 0.0
    assert rates["cv"] == 0.0
    assert rates["tf"] > best_rate
    assert best is None


def test_selector_rejects_unlabelled_or_proxy_only_selection():
    with pytest.raises(ScalingProxyOptInRequired):
        select_best_protocol(40.0, 20, -24.0, protocols=("dv", "tf"))
    with pytest.raises(ValueError, match="eligible"):
        select_best_protocol(
            40.0, 20, -24.0, protocols=("tf",),
            include_scaling_proxies=True)


def test_proxy_optimizer_requires_opt_in_and_labels_result():
    with pytest.raises(ScalingProxyOptInRequired):
        optimize_launch_power(200.0, 20, 1e-6, protocol="tf")
    op = optimize_launch_power(
        200.0, 20, 1e-6, protocol="tf", allow_scaling_proxy=True)
    assert op.feasible
    assert op.secret_key_rate >= 1e-6 * (1 - 1e-2)
    assert op.model_status is ModelStatus.SCALING_PROXY
    assert not op.automatic_recommendation_eligible


def test_finite_key_lowers_coexistence_rate():
    asym = protocol_coexistence_key_rate("dv", 40.0, -24.0, 20)
    fin = protocol_coexistence_key_rate("dv", 40.0, -24.0, 20,
                                        finite=FiniteKeyParams(1e9, 1e-9))
    assert 0.0 <= fin <= asym + 1e-12
