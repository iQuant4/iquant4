from __future__ import annotations

import math

import numpy as np

from ._types import ComplexVector


def coherent_state(
    alpha: complex,
    cutoff: int,
) -> ComplexVector:
    """Create a coherent state |alpha>."""
    if cutoff <= 0:
        raise ValueError(
            "Cutoff must be positive."
        )

    coefficients = np.zeros(
        cutoff,
        dtype=np.complex128,
    )

    prefactor = np.exp(
        -0.5 * abs(alpha) ** 2
    )

    for photon_number in range(cutoff):
        coefficients[photon_number] = (
            prefactor
            * alpha**photon_number
            / math.sqrt(
                math.factorial(photon_number)
            )
        )

    norm = np.linalg.norm(coefficients)

    if norm == 0.0:
        raise ValueError(
            "State normalization is zero."
        )

    return coefficients / norm


__all__ = ["coherent_state"]
