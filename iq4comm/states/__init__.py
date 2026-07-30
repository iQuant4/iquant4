"""Compatibility state namespace for iQuant4Comm.

Reusable state functionality is implemented by :mod:`iqcore.states`.
"""

from .generators import (
    ComplexMatrix,
    ComplexVector,
    approximate_gkp_state,
    coherent_state,
    displaced_squeezed_state,
    even_cat_state,
    fock_state,
    odd_cat_state,
    squeezed_vacuum_state,
    thermal_state,
    two_mode_squeezed_vacuum_state,
)
from .tools import (
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
    "approximate_gkp_state",
    "as_complex_array",
    "coherent_state",
    "density_matrix",
    "displaced_squeezed_state",
    "even_cat_state",
    "fock_state",
    "is_density_matrix",
    "is_ket",
    "is_pure_state",
    "normalize_density_matrix",
    "normalize_ket",
    "odd_cat_state",
    "purity",
    "squeezed_vacuum_state",
    "state_dimension",
    "thermal_state",
    "trace_value",
    "two_mode_squeezed_vacuum_state",
    "validate_quantum_state",
]
