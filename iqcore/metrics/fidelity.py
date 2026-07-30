from __future__ import annotations

import numpy as np

from iqcore.states import (
    ComplexMatrix,
    ComplexVector,
)


def pure_state_fidelity(
    density_matrix: ComplexMatrix,
    target_state: ComplexVector,
) -> float:
    """
    Calculate the fidelity

        F = <psi|rho|psi>

    for a pure target state |psi>.
    """
    density_matrix = np.asarray(
        density_matrix,
        dtype=np.complex128,
    )

    target_state = np.asarray(
        target_state,
        dtype=np.complex128,
    ).reshape(-1)

    if density_matrix.shape != (
        len(target_state),
        len(target_state),
    ):
        raise ValueError(
            "The target state and density matrix "
            "dimensions do not agree."
        )

    state_norm = np.linalg.norm(
        target_state
    )

    if state_norm == 0.0:
        raise ValueError(
            "Target state cannot have zero norm."
        )

    normalized_target = (
        target_state / state_norm
    )

    fidelity = np.real(
        np.vdot(
            normalized_target,
            density_matrix
            @ normalized_target,
        )
    )

    return float(
        np.clip(
            fidelity,
            0.0,
            1.0,
        )
    )


__all__ = ["pure_state_fidelity"]
