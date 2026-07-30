"""
Compatibility layer for the legacy multimode module.

New code should import subsystem utilities from ``iqcore.states``.
"""

from iqcore.states import (
    ComplexMatrix,
    ComplexVector,
    Dimensions,
    QuantumStateArray,
    basis_index,
    basis_occupations,
    density_tensor_product,
    mode_dimension,
    number_of_modes,
    partial_trace,
    product_state_dimensions,
    reduced_state,
    tensor_product,
    total_dimension,
    validate_dimensions,
    validate_state_dimensions,
)

__all__ = [
    "ComplexMatrix",
    "ComplexVector",
    "Dimensions",
    "QuantumStateArray",
    "basis_index",
    "basis_occupations",
    "density_tensor_product",
    "mode_dimension",
    "number_of_modes",
    "partial_trace",
    "product_state_dimensions",
    "reduced_state",
    "tensor_product",
    "total_dimension",
    "validate_dimensions",
    "validate_state_dimensions",
]
