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
from .cv import (
    holevo_g,
    CVDetector,
    cvqkd_homodyne_key_rate,
    cvqkd_rate_vs_distance,
)
from .coexistence import (
    RamanModel,
    raman_background_yield,
    raman_photon_occupation,
    cv_raman_excess_noise,
    coexistence_dv_key_rate,
    coexistence_cv_key_rate,
    classical_capacity_bps,
    coexistence_curve,
    CoexistencePoint,
)
from .finite_key import (
    FiniteKeyParams,
    finite_key_fraction,
)
from .optimize import (
    OperatingPoint,
    optimize_launch_power,
    coexistence_reach,
    protocol_coexistence_key_rate,
    select_best_protocol,
)
from .protocols import (
    mdi_qkd_key_rate,
    tf_qkd_key_rate,
    trusted_node_key_rate,
)

__all__ = [
    "binary_entropy",
    "plob_bound_bits",
    "DetectorModel",
    "bb84_decoy_key_rate",
    "bb84_rate_vs_distance",
    "holevo_g",
    "CVDetector",
    "cvqkd_homodyne_key_rate",
    "cvqkd_rate_vs_distance",
    "RamanModel",
    "raman_background_yield",
    "raman_photon_occupation",
    "cv_raman_excess_noise",
    "coexistence_dv_key_rate",
    "coexistence_cv_key_rate",
    "classical_capacity_bps",
    "coexistence_curve",
    "CoexistencePoint",
    "OperatingPoint",
    "optimize_launch_power",
    "coexistence_reach",
    "protocol_coexistence_key_rate",
    "select_best_protocol",
    "FiniteKeyParams",
    "finite_key_fraction",
    "mdi_qkd_key_rate",
    "tf_qkd_key_rate",
    "trusted_node_key_rate",
]
