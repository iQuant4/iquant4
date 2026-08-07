"""Model-maturity labels must remain explicit and machine-readable."""

from __future__ import annotations

import dataclasses

import pytest

from iq4comm.qkd import (
    AUTO_SELECTION_PROTOCOLS,
    FINITE_KEY_MODEL,
    PROTOCOL_MODEL_INFO,
    REPEATER_MODEL,
    SCALING_PROXY_PROTOCOLS,
    FiniteKeyParams,
    ModelStatus,
    optimal_segment_count,
    protocol_model_info,
)


def test_protocol_registry_separates_research_models_from_scaling_proxies():
    assert AUTO_SELECTION_PROTOCOLS == ("dv", "cv")
    assert SCALING_PROXY_PROTOCOLS == ("mdi", "tf")
    for protocol in AUTO_SELECTION_PROTOCOLS:
        info = protocol_model_info(protocol)
        assert info.status is ModelStatus.RESEARCH_MODEL
        assert info.automatic_recommendation_eligible
    for protocol in SCALING_PROXY_PROTOCOLS:
        info = protocol_model_info(protocol)
        assert info.status is ModelStatus.SCALING_PROXY
        assert not info.automatic_recommendation_eligible


def test_protocol_registry_is_read_only_and_rejects_unknown_protocols():
    with pytest.raises(TypeError):
        PROTOCOL_MODEL_INFO["invented"] = PROTOCOL_MODEL_INFO["dv"]  # type: ignore[index]
    with pytest.raises(ValueError, match="protocol"):
        protocol_model_info("invented")


def test_finite_size_params_carry_sensitivity_label():
    params = FiniteKeyParams()
    assert params.model_status is ModelStatus.SENSITIVITY_ESTIMATE
    assert FINITE_KEY_MODEL.status is ModelStatus.SENSITIVITY_ESTIMATE
    assert dataclasses.asdict(params)["model_status"] is ModelStatus.SENSITIVITY_ESTIMATE


def test_repeater_results_carry_scaling_proxy_label():
    result = optimal_segment_count(200.0)
    assert result.model_status is ModelStatus.SCALING_PROXY
    assert REPEATER_MODEL.status is ModelStatus.SCALING_PROXY
    assert not REPEATER_MODEL.automatic_recommendation_eligible
