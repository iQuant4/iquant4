"""Compatibility layer for bosonic operators.

The canonical implementation lives in :mod:`iqcore.operators`.
"""

from iqcore.operators import (
    annihilation_operator,
    displacement_operator,
    squeezing_operator,
)

__all__ = [
    "annihilation_operator",
    "displacement_operator",
    "squeezing_operator",
]
