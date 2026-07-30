from __future__ import annotations

import numpy as np

from ._types import ComplexMatrix


def thermal_state(
    mean_photon_number: float,
    cutoff: int,
) -> ComplexMatrix:
    """Create a truncated single-mode thermal density matrix."""
    if mean_photon_number < 0.0:
        raise ValueError(
            "Mean photon number cannot be negative."
        )

    if cutoff <= 0:
        raise ValueError(
            "Cutoff must be positive."
        )

    probabilities = np.zeros(
        cutoff,
        dtype=np.float64,
    )

    if mean_photon_number == 0.0:
        probabilities[0] = 1.0
    else:
        ratio = (
            mean_photon_number
            / (1.0 + mean_photon_number)
        )

        prefactor = (
            1.0
            / (1.0 + mean_photon_number)
        )

        for photon_number in range(cutoff):
            probabilities[photon_number] = (
                prefactor
                * ratio**photon_number
            )

        probability_sum = np.sum(
            probabilities
        )

        if probability_sum == 0.0:
            raise ValueError(
                "Thermal-state normalization is zero."
            )

        probabilities /= probability_sum

    return np.diag(
        probabilities.astype(
            np.complex128
        )
    )


__all__ = ["thermal_state"]
