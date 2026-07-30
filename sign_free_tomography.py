"""Compatibility layer for legacy sign-free tomography imports.

New code should import measurements from ``iqcore.measurements``,
metrics from ``iqcore.metrics``, and reconstruction algorithms from
``iqcore.tomography``.
"""

from iqcore.measurements import (
    build_measurement_operators,
    histogram_probabilities,
    integrate_sign_free_povm_bin,
    quadrature_bra_coefficients,
    sign_free_povm_density,
)
from iqcore.metrics import pure_state_fidelity
from iqcore.states import (
    ComplexMatrix,
    ComplexVector,
)
from iqcore.tomography import (
    RealVector,
    TomographyResult,
    build_linear_measurement_matrix,
    reconstruct_density_matrix,
    validate_measurement_matrix,
)

__all__ = [
    "ComplexMatrix",
    "ComplexVector",
    "RealVector",
    "TomographyResult",
    "build_linear_measurement_matrix",
    "build_measurement_operators",
    "histogram_probabilities",
    "integrate_sign_free_povm_bin",
    "pure_state_fidelity",
    "quadrature_bra_coefficients",
    "reconstruct_density_matrix",
    "sign_free_povm_density",
    "validate_measurement_matrix",
]
