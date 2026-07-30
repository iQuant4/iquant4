from __future__ import annotations

import numpy as np

from ._types import QuantumStateArray, as_complex_array
from .validation import density_matrix


def state_dimension(
    state: QuantumStateArray,
) -> int:
    """Return the Hilbert-space dimension."""
    rho = density_matrix(state)

    return int(rho.shape[0])


def trace_value(
    state: QuantumStateArray,
) -> complex:
    """Return the trace of the normalized density matrix."""
    return complex(
        np.trace(
            density_matrix(state)
        )
    )


def purity(
    state: QuantumStateArray,
) -> float:
    """Calculate the state purity Tr(rho^2)."""
    rho = density_matrix(state)

    value = np.real(
        np.trace(rho @ rho)
    )

    return float(value)


def is_pure_state(
    state: QuantumStateArray,
    *,
    tolerance: float = 1e-8,
) -> bool:
    """Determine whether a state is pure."""
    return bool(
        np.isclose(
            purity(state),
            1.0,
            atol=tolerance,
        )
    )


def validate_quantum_state(
    state: QuantumStateArray,
) -> dict[str, object]:
    """Return basic validation information for a quantum state."""
    state_array = as_complex_array(state)
    rho = density_matrix(state)

    eigenvalues = np.linalg.eigvalsh(rho)

    return {
        "representation": (
            "ket"
            if state_array.ndim == 1
            else "density_matrix"
        ),
        "dimension": int(rho.shape[0]),
        "trace": complex(np.trace(rho)),
        "hermiticity_error": float(
            np.linalg.norm(
                rho - rho.conjugate().T
            )
        ),
        "minimum_eigenvalue": float(
            np.min(np.real(eigenvalues))
        ),
        "purity": purity(rho),
        "is_pure": is_pure_state(rho),
    }
