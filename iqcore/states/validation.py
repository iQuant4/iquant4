from __future__ import annotations

import numpy as np

from ._types import (
    ComplexMatrix,
    ComplexVector,
    QuantumStateArray,
    as_complex_array,
)


def is_ket(
    state: QuantumStateArray,
) -> bool:
    """Return True when the input is a one-dimensional ket."""
    return as_complex_array(state).ndim == 1


def is_density_matrix(
    state: QuantumStateArray,
) -> bool:
    """Return True when the input is a square matrix."""
    state_array = as_complex_array(state)

    return (
        state_array.ndim == 2
        and state_array.shape[0] == state_array.shape[1]
    )


def normalize_ket(
    state: QuantumStateArray,
) -> ComplexVector:
    """Return a normalized state vector."""
    state_array = as_complex_array(state)

    if state_array.ndim != 1:
        raise ValueError(
            "A ket must be one-dimensional."
        )

    norm = np.linalg.norm(state_array)

    if np.isclose(norm, 0.0):
        raise ValueError(
            "Ket normalization is zero."
        )

    return state_array / norm


def normalize_density_matrix(
    state: QuantumStateArray,
    *,
    hermiticity_tolerance: float = 1e-8,
    positivity_tolerance: float = 1e-10,
) -> ComplexMatrix:
    """
    Validate and normalize a density matrix.

    The matrix must be square, Hermitian, have nonzero trace,
    and be positive semidefinite within numerical tolerance.
    """
    state_array = as_complex_array(state)

    if state_array.ndim != 2:
        raise ValueError(
            "A density matrix must be two-dimensional."
        )

    rows, columns = state_array.shape

    if rows != columns:
        raise ValueError(
            "A density matrix must be square."
        )

    trace = np.trace(state_array)

    if np.isclose(abs(trace), 0.0):
        raise ValueError(
            "Density-matrix trace is zero."
        )

    normalized_matrix = state_array / trace

    hermiticity_error = np.linalg.norm(
        normalized_matrix
        - normalized_matrix.conjugate().T
    )

    if hermiticity_error > hermiticity_tolerance:
        raise ValueError(
            "Density matrix must be Hermitian."
        )

    normalized_matrix = 0.5 * (
        normalized_matrix
        + normalized_matrix.conjugate().T
    )

    eigenvalues = np.linalg.eigvalsh(
        normalized_matrix
    )

    minimum_eigenvalue = float(
        np.min(np.real(eigenvalues))
    )

    if minimum_eigenvalue < -positivity_tolerance:
        raise ValueError(
            "Density matrix must be positive semidefinite. "
            f"Minimum eigenvalue: {minimum_eigenvalue:.3e}"
        )

    return normalized_matrix


def density_matrix(
    state: QuantumStateArray,
) -> ComplexMatrix:
    """
    Convert a ket or density matrix into a normalized density matrix.

    For a ket |psi>, this returns rho = |psi><psi|.
    A density-matrix input is validated and normalized.
    """
    state_array = as_complex_array(state)

    if state_array.ndim == 1:
        normalized_state = normalize_ket(
            state_array
        )

        return np.outer(
            normalized_state,
            normalized_state.conjugate(),
        )

    if state_array.ndim == 2:
        return normalize_density_matrix(
            state_array
        )

    raise ValueError(
        "State must be a one-dimensional ket or a "
        "two-dimensional density matrix."
    )
