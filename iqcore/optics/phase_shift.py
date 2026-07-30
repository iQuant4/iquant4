from __future__ import annotations

import numpy as np

from iqcore.states import (
    ComplexMatrix,
    QuantumStateArray,
    density_matrix,
)


def phase_shift_operator(
    phase: float,
    cutoff: int,
) -> ComplexMatrix:
    """
    Construct the single-mode optical phase-shift operator.

        U(phi)|n> = exp(i n phi)|n>.
    """
    if cutoff <= 0:
        raise ValueError(
            "Cutoff must be positive."
        )

    photon_numbers = np.arange(
        cutoff,
        dtype=np.float64,
    )

    diagonal_elements = np.exp(
        1j * phase * photon_numbers
    )

    return np.diag(
        diagonal_elements.astype(np.complex128)
    )


def phase_shift_channel(
    state: QuantumStateArray,
    phase: float,
) -> ComplexMatrix:
    """
    Apply a single-mode phase shift.

        rho_out = U(phi) rho_in U(phi)^dagger.
    """
    rho_input = density_matrix(state)

    operator = phase_shift_operator(
        phase=phase,
        cutoff=rho_input.shape[0],
    )

    rho_output = (
        operator
        @ rho_input
        @ operator.conjugate().T
    )

    return np.asarray(
        0.5 * (
            rho_output
            + rho_output.conjugate().T
        ),
        dtype=np.complex128,
    )


__all__ = [
    "phase_shift_channel",
    "phase_shift_operator",
]
