from __future__ import annotations

import numpy as np

from iqcore.states import ComplexMatrix


def build_linear_measurement_matrix(
    measurement_operators: list[ComplexMatrix],
    cutoff: int,
) -> ComplexMatrix:
    """
    Convert the POVM operators into one linear matrix A.

    With row-major vectorization,

        Tr(E_i rho)
        =
        A[i] @ vec(rho).

    Since

        Tr(E rho)
        =
        sum_{m,n} E[n,m] rho[m,n],

    row i of A is the row-major vectorization of E_i.T.
    """
    if cutoff <= 0:
        raise ValueError(
            "Cutoff must be positive."
        )

    if len(measurement_operators) == 0:
        raise ValueError(
            "At least one measurement operator is required."
        )

    expected_shape = (
        cutoff,
        cutoff,
    )

    measurement_matrix = np.empty(
        (
            len(measurement_operators),
            cutoff * cutoff,
        ),
        dtype=np.complex128,
    )

    for index, operator in enumerate(
        measurement_operators
    ):
        operator_array = np.asarray(
            operator,
            dtype=np.complex128,
        )

        if operator_array.shape != expected_shape:
            raise ValueError(
                f"Measurement operator {index} has shape "
                f"{operator_array.shape}; expected "
                f"{expected_shape}."
            )

        measurement_matrix[index, :] = (
            operator_array.T.reshape(
                cutoff * cutoff,
                order="C",
            )
        )

    return measurement_matrix

def validate_measurement_matrix(
    measurement_operators: list[ComplexMatrix],
    density_matrix: ComplexMatrix,
    cutoff: int,
) -> float:
    """
    Confirm that direct trace evaluation and the
    vectorized measurement calculation give the same
    probabilities.

    Returns the maximum absolute difference.
    """
    density_matrix = np.asarray(
        density_matrix,
        dtype=np.complex128,
    )

    if density_matrix.shape != (
        cutoff,
        cutoff,
    ):
        raise ValueError(
            "Density matrix has an incorrect shape."
        )

    direct_probabilities = np.asarray(
        [
            np.real(
                np.trace(
                    operator @ density_matrix
                )
            )
            for operator in measurement_operators
        ],
        dtype=float,
    )

    measurement_matrix = (
        build_linear_measurement_matrix(
            measurement_operators=(
                measurement_operators
            ),
            cutoff=cutoff,
        )
    )

    density_vector = density_matrix.reshape(
        cutoff * cutoff,
        order="C",
    )

    vectorized_probabilities = np.real(
        measurement_matrix
        @ density_vector
    )

    maximum_difference = np.max(
        np.abs(
            direct_probabilities
            - vectorized_probabilities
        )
    )

    return float(maximum_difference)


__all__ = [
    "build_linear_measurement_matrix",
    "validate_measurement_matrix",
]
