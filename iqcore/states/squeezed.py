from __future__ import annotations

import numpy as np

from iqcore.operators import (
    displacement_operator,
    squeezing_operator,
)

from ._types import ComplexVector
from .fock import fock_state


def squeezed_vacuum_state(
    squeezing_magnitude: float,
    squeezing_phase: float,
    cutoff: int,
) -> ComplexVector:
    """Create a normalized single-mode squeezed-vacuum state."""
    if squeezing_magnitude < 0.0:
        raise ValueError(
            "Squeezing magnitude cannot be negative."
        )

    if cutoff <= 0:
        raise ValueError(
            "Cutoff must be positive."
        )

    xi = (
        squeezing_magnitude
        * np.exp(1j * squeezing_phase)
    )

    vacuum = fock_state(
        photon_number=0,
        cutoff=cutoff,
    )

    state = (
        squeezing_operator(
            xi=xi,
            cutoff=cutoff,
        )
        @ vacuum
    )

    norm = np.linalg.norm(state)

    if norm == 0.0:
        raise ValueError(
            "Squeezed-vacuum normalization is zero."
        )

    return state / norm


def displaced_squeezed_state(
    alpha: complex,
    squeezing_magnitude: float,
    squeezing_phase: float,
    cutoff: int,
) -> ComplexVector:
    """
    Create a normalized displaced squeezed state.

        |alpha, xi> = D(alpha) S(xi) |0>.
    """
    if squeezing_magnitude < 0.0:
        raise ValueError(
            "Squeezing magnitude cannot be negative."
        )

    if cutoff <= 0:
        raise ValueError(
            "Cutoff must be positive."
        )

    squeezed_vacuum = squeezed_vacuum_state(
        squeezing_magnitude=squeezing_magnitude,
        squeezing_phase=squeezing_phase,
        cutoff=cutoff,
    )

    state = (
        displacement_operator(
            alpha=alpha,
            cutoff=cutoff,
        )
        @ squeezed_vacuum
    )

    norm = np.linalg.norm(state)

    if norm == 0.0:
        raise ValueError(
            "Displaced squeezed-state normalization is zero."
        )

    return state / norm


__all__ = [
    "displaced_squeezed_state",
    "squeezed_vacuum_state",
]
