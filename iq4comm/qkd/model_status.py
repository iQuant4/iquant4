"""Machine-readable maturity labels for iQuant4 QKD models.

Scientific software must distinguish a useful scaling law from a protocol
implementation that is suitable for a design recommendation.  This module is
the canonical registry for that distinction.  Labels are deliberately about
the *implemented model*, not about the underlying protocol or research field.

``research_model``
    A reduced model that may participate in comparative platform workflows
    inside its documented assumptions.  This is not a claim of independent
    experimental validation or engineering-grade accuracy.

``scaling_proxy``
    A qualitative/asymptotic scaling model.  It may be plotted or explored but
    is excluded from automatic engineering recommendations.

``sensitivity_estimate``
    A generic penalty used to study trends.  It is not a protocol-specific,
    composable security proof.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from types import MappingProxyType
from typing import Mapping

__all__ = [
    "ModelStatus",
    "ModelMetadata",
    "DV_MODEL",
    "CV_MODEL",
    "MDI_MODEL",
    "TF_MODEL",
    "TRUSTED_NODE_MODEL",
    "REPEATER_MODEL",
    "FINITE_KEY_MODEL",
    "PROTOCOL_MODEL_INFO",
    "AUTO_SELECTION_PROTOCOLS",
    "SCALING_PROXY_PROTOCOLS",
    "protocol_model_info",
    "ScalingProxyOptInRequired",
    "require_scaling_proxy_opt_in",
]


class ModelStatus(str, Enum):
    """Maturity of an implemented numerical model."""

    RESEARCH_MODEL = "research_model"
    SCALING_PROXY = "scaling_proxy"
    SENSITIVITY_ESTIMATE = "sensitivity_estimate"


class ScalingProxyOptInRequired(ValueError):
    """Raised when a high-level workflow is asked to use a scaling proxy."""


@dataclass(frozen=True)
class ModelMetadata:
    """Maturity and recommendation eligibility for one implemented model."""

    key: str
    display_name: str
    status: ModelStatus
    automatic_recommendation_eligible: bool
    scope: str

    @property
    def is_proxy(self) -> bool:
        return self.status is ModelStatus.SCALING_PROXY


DV_MODEL = ModelMetadata(
    key="dv",
    display_name="Decoy-state DV-BB84",
    status=ModelStatus.RESEARCH_MODEL,
    automatic_recommendation_eligible=True,
    scope="Reduced asymptotic key-rate model with calibrated coexistence noise.",
)

CV_MODEL = ModelMetadata(
    key="cv",
    display_name="GG02 homodyne CV-QKD",
    status=ModelStatus.RESEARCH_MODEL,
    automatic_recommendation_eligible=True,
    scope="Reduced asymptotic Gaussian-channel model within declared detector assumptions.",
)

MDI_MODEL = ModelMetadata(
    key="mdi",
    display_name="MDI-QKD scaling model",
    status=ModelStatus.SCALING_PROXY,
    automatic_recommendation_eligible=False,
    scope="Coincidence and eta-scaling proxy; no full decoy-state parameter estimation.",
)

TF_MODEL = ModelMetadata(
    key="tf",
    display_name="Twin-field QKD scaling model",
    status=ModelStatus.SCALING_PROXY,
    automatic_recommendation_eligible=False,
    scope="Square-root-transmittance proxy; no protocol-specific security or phase model.",
)

TRUSTED_NODE_MODEL = ModelMetadata(
    key="trusted_node",
    display_name="Trusted-node chain scaling model",
    status=ModelStatus.SCALING_PROXY,
    automatic_recommendation_eligible=False,
    scope="Equal-segment rate proxy without node operations, scheduling, or availability.",
)

REPEATER_MODEL = ModelMetadata(
    key="repeater",
    display_name="Memory-assisted repeater scaling model",
    status=ModelStatus.SCALING_PROXY,
    automatic_recommendation_eligible=False,
    scope="Werner-state and deterministic-rate proxy without memory waiting-time statistics.",
)

FINITE_KEY_MODEL = ModelMetadata(
    key="finite_key",
    display_name="Generic finite-size sensitivity estimate",
    status=ModelStatus.SENSITIVITY_ESTIMATE,
    automatic_recommendation_eligible=False,
    scope="Generic Hoeffding penalty; not a protocol-specific composable finite-key proof.",
)

PROTOCOL_MODEL_INFO: Mapping[str, ModelMetadata] = MappingProxyType({
    "dv": DV_MODEL,
    "cv": CV_MODEL,
    "mdi": MDI_MODEL,
    "tf": TF_MODEL,
})

AUTO_SELECTION_PROTOCOLS = tuple(
    key for key, info in PROTOCOL_MODEL_INFO.items()
    if info.automatic_recommendation_eligible
)

SCALING_PROXY_PROTOCOLS = tuple(
    key for key, info in PROTOCOL_MODEL_INFO.items() if info.is_proxy
)


def protocol_model_info(protocol: str) -> ModelMetadata:
    """Return canonical model metadata for a protocol key."""
    key = protocol.lower()
    try:
        return PROTOCOL_MODEL_INFO[key]
    except KeyError as exc:
        choices = ", ".join(PROTOCOL_MODEL_INFO)
        raise ValueError(f"protocol must be one of {choices}") from exc


def require_scaling_proxy_opt_in(protocol: str, *,
                                 allow_scaling_proxy: bool) -> ModelMetadata:
    """Validate a protocol and enforce explicit proxy use in high-level APIs."""
    info = protocol_model_info(protocol)
    if info.is_proxy and not allow_scaling_proxy:
        raise ScalingProxyOptInRequired(
            f"{info.key!r} is implemented as a scaling_proxy. "
            "Pass allow_scaling_proxy=True only for exploratory comparison; "
            "scaling proxies remain ineligible for automatic recommendations."
        )
    return info
