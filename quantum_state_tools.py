"""
Compatibility layer for the legacy quantum_state_tools module.

New code should import these utilities from iqcore.states.
"""

from iqcore.states import (
    ComplexMatrix,
    ComplexVector,
    QuantumStateArray,
    as_complex_array,
    density_matrix,
    is_density_matrix,
    is_ket,
    is_pure_state,
    normalize_density_matrix,
    normalize_ket,
    purity,
    state_dimension,
    trace_value,
    validate_quantum_state,
)

__all__ = [
    "ComplexMatrix",
    "ComplexVector",
    "QuantumStateArray",
    "as_complex_array",
    "density_matrix",
    "is_density_matrix",
    "is_ket",
    "is_pure_state",
    "normalize_density_matrix",
    "normalize_ket",
    "purity",
    "state_dimension",
    "trace_value",
    "validate_quantum_state",
]
