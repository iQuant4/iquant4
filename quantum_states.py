"""
Compatibility layer for the legacy quantum_states module.

New code should import state generators from iqcore.states
and operators from iqcore.operators.
"""

from iqcore.operators import (
    annihilation_operator,
    displacement_operator,
    squeezing_operator,
)
from iqcore.states import (
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

__all__ = [
    "ComplexMatrix",
    "ComplexVector",
    "annihilation_operator",
    "approximate_gkp_state",
    "coherent_state",
    "displaced_squeezed_state",
    "displacement_operator",
    "even_cat_state",
    "fock_state",
    "odd_cat_state",
    "squeezed_vacuum_state",
    "squeezing_operator",
    "thermal_state",
    "two_mode_squeezed_vacuum_state",
]
