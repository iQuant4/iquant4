"""Quantum key distribution for the iQuant4 platform.

Key-rate models that sit directly on the shared fiber foundation: the same
:class:`iqcore.fiber.FiberSpec` transmissivity that drives the classical link
also parametrises the QKD secret-key rate, so classical and quantum performance
are computed from one physical description of the fiber -- including their
coexistence coupling (:mod:`iq4comm.qkd.coexistence`).
"""

from .dv import (
    binary_entropy,
    plob_bound_bits,
    DetectorModel,
    bb84_decoy_key_rate,
    bb84_rate_vs_distance,
)
from .coexistence import (
    RamanModel,
    raman_background_yield,
    coexistence_dv_key_rate,
    classical_capacity_bps,
    coexistence_curve,
    CoexistencePoint,
)

__all__ = [
    "binary_entropy",
    "plob_bound_bits",
    "DetectorModel",
    "bb84_decoy_key_rate",
    "bb84_rate_vs_distance",
    "RamanModel",
    "raman_background_yield",
    "coexistence_dv_key_rate",
    "classical_capacity_bps",
    "coexistence_curve",
    "CoexistencePoint",
]
