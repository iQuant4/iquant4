from __future__ import annotations

import numpy as np

from ._types import ComplexVector


def two_mode_squeezed_vacuum_state(
    squeezing_magnitude: float,
    squeezing_phase: float,
    cutoff: int,
) -> ComplexVector:
    """
    Create a truncated two-mode squeezed-vacuum state.

    The state is

        |TMSV> =
        sqrt(1 - lambda^2)
        sum_n lambda^n exp(i n phi) |n,n>,

    with

        lambda = tanh(r).

    The returned vector has length cutoff**2 and uses the
    tensor-product ordering

        |n_A, n_B>.

    The basis index is

        index = n_A * cutoff + n_B.
    """
    if squeezing_magnitude < 0.0:
        raise ValueError(
            "Squeezing magnitude cannot be negative."
        )

    if cutoff <= 0:
        raise ValueError(
            "Cutoff must be positive."
        )

    lambda_parameter = np.tanh(
        squeezing_magnitude
    )

    state = np.zeros(
        cutoff * cutoff,
        dtype=np.complex128,
    )

    prefactor = np.sqrt(
        1.0 - lambda_parameter**2
    )

    for photon_number in range(cutoff):
        coefficient = (
            prefactor
            * lambda_parameter**photon_number
            * np.exp(
                1j
                * photon_number
                * squeezing_phase
            )
        )

        basis_index = (
            photon_number * cutoff
            + photon_number
        )

        state[basis_index] = coefficient

    norm = np.linalg.norm(state)

    if norm == 0.0:
        raise ValueError(
            "Two-mode squeezed-vacuum normalization is zero."
        )

    return state / norm
