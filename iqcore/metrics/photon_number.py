from __future__ import annotations

import numpy as np
from numpy.typing import NDArray

from iqcore.states import (
    QuantumStateArray,
    density_matrix,
    purity,
)


def photon_number_distribution(
    state: QuantumStateArray,
) -> NDArray[np.float64]:
    """
    Compute a normalized photon-number probability distribution.

    For a state vector, ``P(n) = |c_n|^2``. For a density
    matrix, ``P(n) = rho[n, n]``.
    """
    rho = density_matrix(state)

    probabilities = np.real(
        np.diag(rho)
    ).astype(np.float64)

    numerical_tolerance = 1e-12

    probabilities[
        np.abs(probabilities)
        < numerical_tolerance
    ] = 0.0

    if np.any(
        probabilities < -numerical_tolerance
    ):
        raise ValueError(
            "The state contains negative photon-number "
            "probabilities."
        )

    probabilities = np.clip(
        probabilities,
        0.0,
        None,
    )

    probability_sum = float(
        np.sum(probabilities)
    )

    if np.isclose(
        probability_sum,
        0.0,
    ):
        raise ValueError(
            "Photon-number probabilities sum to zero."
        )

    return probabilities / probability_sum


def mean_photon_number(
    state: QuantumStateArray,
) -> float:
    """Calculate the mean photon number ``sum_n n P(n)``."""
    probabilities = photon_number_distribution(
        state
    )

    photon_numbers = np.arange(
        probabilities.size,
        dtype=np.float64,
    )

    return float(
        np.sum(
            photon_numbers
            * probabilities
        )
    )


def photon_number_variance(
    state: QuantumStateArray,
) -> float:
    """Calculate ``Var(n) = <n^2> - <n>^2``."""
    probabilities = photon_number_distribution(
        state
    )

    photon_numbers = np.arange(
        probabilities.size,
        dtype=np.float64,
    )

    mean = np.sum(
        photon_numbers
        * probabilities
    )

    second_moment = np.sum(
        photon_numbers**2
        * probabilities
    )

    variance = (
        second_moment
        - mean**2
    )

    if (
        variance < 0.0
        and np.isclose(
            variance,
            0.0,
            atol=1e-12,
        )
    ):
        variance = 0.0

    return float(variance)


def state_purity(
    state: QuantumStateArray,
) -> float:
    """Calculate the state purity ``Tr(rho^2)``."""
    return purity(state)


__all__ = [
    "mean_photon_number",
    "photon_number_distribution",
    "photon_number_variance",
    "state_purity",
]
