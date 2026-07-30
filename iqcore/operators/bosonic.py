from __future__ import annotations

import numpy as np
from scipy.linalg import expm

from numpy.typing import NDArray

ComplexMatrix = NDArray[np.complex128]


def annihilation_operator(
    cutoff: int,
) -> ComplexMatrix:
    """Return the truncated annihilation operator."""
    if cutoff <= 0:
        raise ValueError(
            "Cutoff must be positive."
        )

    operator = np.zeros(
        (cutoff, cutoff),
        dtype=np.complex128,
    )

    for photon_number in range(1, cutoff):
        operator[
            photon_number - 1,
            photon_number,
        ] = np.sqrt(photon_number)

    return operator


def displacement_operator(
    alpha: complex,
    cutoff: int,
) -> ComplexMatrix:
    """
    Return the truncated displacement operator

        D(alpha) = exp(alpha a† - alpha* a).
    """
    a = annihilation_operator(
        cutoff=cutoff,
    )

    a_dagger = a.conjugate().T

    generator = (
        alpha * a_dagger
        - np.conjugate(alpha) * a
    )

    return expm(generator)


def squeezing_operator(
    xi: complex,
    cutoff: int,
) -> ComplexMatrix:
    """
    Return the truncated squeezing operator

        S(xi) =
        exp[1/2 (xi a^2 - xi* a†^2)].

    This follows the convention used in the original
    implementation.
    """
    a = annihilation_operator(
        cutoff=cutoff,
    )

    a_dagger = a.conjugate().T

    generator = 0.5 * (
        xi * (a @ a)
        - np.conjugate(xi)
        * (a_dagger @ a_dagger)
    )

    return expm(generator)


__all__ = [
    "annihilation_operator",
    "displacement_operator",
    "squeezing_operator",
]
