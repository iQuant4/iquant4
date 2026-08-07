"""Reach-extension QKD protocols: MDI-QKD, Twin-Field QKD, trusted-node relay.

Because a quantum signal cannot be amplified (no-cloning: any gain adds enough
noise to break security), QKD reach cannot be extended with inline EDFAs the way
classical DWDM is.  The realistic options are different *protocols* and
*architectures*, all modelled here on the same :class:`iqcore.fiber.FiberSpec`:

* :func:`mdi_qkd_key_rate` -- Measurement-Device-Independent QKD.  A central
  *untrusted* relay performs a Bell measurement on photons from Alice and Bob;
  the two-photon coincidence makes the rate scale as ``eta`` (like BB84) but
  immune to all detector side-channels.
* :func:`tf_qkd_key_rate` -- Twin-Field QKD.  Single-photon interference at a
  central node makes the rate scale as ``sqrt(eta)``, which **beats the PLOB
  repeaterless bound** and roughly doubles the reach -- with no quantum memory
  or repeater.
* :func:`trusted_node_key_rate` -- a chain of trusted intermediate nodes.  Each
  amplifier-free segment runs a base protocol and the key is relayed hop by hop,
  so *any* distance is reachable -- at the cost of trusting the nodes.

The rate models are simplified asymptotic forms that capture the essential
scaling (the ``eta`` vs ``sqrt(eta)`` distinction and the PLOB crossing); they
are not full decoy-state finite-key analyses.

References: Braunstein & Pirandola (MDI, 2012); Lo, Curty & Qi (MDI, 2012);
Lucamarini et al., "Overcoming the rate-distance limit of QKD without quantum
repeaters," Nature 557, 400 (2018) (Twin-Field).
"""

from __future__ import annotations

from math import sqrt

from iqcore.fiber import FiberSpec, SMF28
from .dv import DetectorModel, bb84_decoy_key_rate
from .finite_key import FiniteKeyParams, finite_key_fraction
from .model_status import MDI_MODEL, TF_MODEL, TRUSTED_NODE_MODEL

__all__ = [
    "mdi_qkd_key_rate",
    "tf_qkd_key_rate",
    "trusted_node_key_rate",
    "MDI_MODEL",
    "TF_MODEL",
    "TRUSTED_NODE_MODEL",
]


def mdi_qkd_key_rate(transmissivity: float, *,
                     detector: DetectorModel | None = None,
                     background_yield: float = 0.0,
                     finite: FiniteKeyParams | None = None) -> float:
    """MDI-QKD *scaling-proxy* rate (bits/pulse).

    Central untrusted relay at the midpoint: the single-photon Bell-measurement
    coincidence scales as the *product* of the two arm transmittances, i.e. as
    the full-path ``transmissivity`` (like BB84), with a coincidence penalty.
    ``background_yield`` injects extra relay-detector clicks (the coexistence
    hook); ``finite`` switches on the generic finite-size sensitivity estimate.
    This implementation is labelled ``scaling_proxy`` and is not eligible for
    automatic engineering recommendations.
    """
    det = detector or DetectorModel()
    eta = transmissivity
    # Two-photon coincidence: (eta_d * sqrt(eta))^2 = eta_d^2 * eta, x1/2 relay.
    t_eff = 0.5 * det.efficiency ** 2 * eta
    y0 = 2.0 * det.dark_count_prob + background_yield
    gain = y0 + t_eff
    error = (0.5 * y0 + det.misalignment * t_eff) / gain if gain > 0 else 0.5
    return finite_key_fraction(gain, error,
                               error_correction_eff=det.error_correction_eff,
                               params=finite)


def tf_qkd_key_rate(transmissivity: float, *,
                    detector: DetectorModel | None = None,
                    interferometric_error: float = 0.02,
                    protocol_efficiency: float = 0.25,
                    background_yield: float = 0.0,
                    finite: FiniteKeyParams | None = None) -> float:
    """Twin-field QKD *scaling-proxy* rate (bits/pulse).

    Single-photon interference at a central node: a click needs only *one* photon
    to reach the midpoint, so the rate scales as ``sqrt(eta)`` and can exceed the
    PLOB repeaterless bound.  ``protocol_efficiency`` (< 1) is the fraction of
    events that yield key after phase post-selection / the sending fraction --
    it is why TF-QKD is *lower* than direct BB84 at short range and only wins
    once ``sqrt(eta)`` overtakes ``eta`` at long range.  ``interferometric_error``
    is the phase-stability penalty; ``background_yield`` is the coexistence hook;
    ``finite`` switches on the generic finite-size sensitivity estimate.  This
    implementation is labelled ``scaling_proxy`` and is not a protocol-specific
    security analysis or an automatic-recommendation candidate.
    """
    det = detector or DetectorModel()
    eta = transmissivity
    t_eff = protocol_efficiency * det.efficiency * sqrt(eta)   # sqrt(eta) scaling
    y0 = 2.0 * det.dark_count_prob + background_yield
    gain = y0 + t_eff
    e_d = det.misalignment + interferometric_error
    error = (0.5 * y0 + e_d * t_eff) / gain if gain > 0 else 0.5
    return finite_key_fraction(gain, error,
                               error_correction_eff=det.error_correction_eff,
                               params=finite)


def trusted_node_key_rate(distance_km: float, n_nodes: int, *,
                          fiber: FiberSpec = SMF28, protocol: str = "dv",
                          detector: DetectorModel | None = None,
                          mu: float = 0.5) -> float:
    """End-to-end *scaling-proxy* rate through trusted intermediate nodes.

    The link is split into ``n_nodes + 1`` equal amplifier-free segments; each
    runs the base ``protocol`` and the key is relayed, so the end-to-end rate is
    the (identical) per-segment rate.  Adding nodes shortens each segment and
    lifts the rate -- reaching any distance, if the nodes can be trusted.  Node
    operations, scheduling, availability, and key-management constraints are
    outside this proxy.
    """
    if n_nodes < 0:
        raise ValueError("n_nodes must be non-negative")
    n_segments = n_nodes + 1
    seg_len = distance_km / n_segments
    eta_seg = fiber.transmissivity(seg_len)
    proto = protocol.lower()
    if proto == "dv":
        return bb84_decoy_key_rate(eta_seg, mu, detector=detector)
    if proto == "tf":
        return tf_qkd_key_rate(eta_seg, detector=detector)
    if proto == "mdi":
        return mdi_qkd_key_rate(eta_seg, detector=detector)
    raise ValueError("protocol must be 'dv', 'tf', or 'mdi'")
