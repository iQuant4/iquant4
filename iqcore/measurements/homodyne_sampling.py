from __future__ import annotations

import math

import numpy as np
from numpy.typing import NDArray
from scipy.special import eval_hermite

from iqcore.states import ComplexVector


RealVector = NDArray[np.float64]


def quadrature_wavefunction(
    state: ComplexVector,
    x_values: RealVector,
    phase: float,
) -> NDArray[np.complex128]:
    """
    Compute <x_phi|psi> for a pure state represented in the
    truncated Fock basis.
    """
    x_array = np.asarray(
        x_values,
        dtype=float,
    )
    state_array = np.asarray(
        state,
        dtype=np.complex128,
    )

    if state_array.ndim != 1:
        raise ValueError(
            "State must be a one-dimensional ket."
        )

    wavefunction = np.zeros(
        x_array.shape,
        dtype=np.complex128,
    )

    gaussian_factor = (
        np.pi ** (-0.25)
        * np.exp(-0.5 * x_array**2)
    )

    for photon_number, coefficient in enumerate(
        state_array
    ):
        normalization = math.sqrt(
            (2.0**photon_number)
            * math.factorial(photon_number)
        )

        fock_wavefunction = (
            gaussian_factor
            * eval_hermite(
                photon_number,
                x_array,
            )
            / normalization
        )

        wavefunction += (
            coefficient
            * np.exp(-1j * photon_number * phase)
            * fock_wavefunction
        )

    return wavefunction


def quadrature_probability_density(
    state: ComplexVector,
    x_values: RealVector,
    phase: float,
) -> RealVector:
    """Compute the normalized pure-state quadrature density."""
    x_array = np.asarray(
        x_values,
        dtype=float,
    )

    probability_density = np.abs(
        quadrature_wavefunction(
            state=state,
            x_values=x_array,
            phase=phase,
        )
    ) ** 2

    normalization = np.trapezoid(
        probability_density,
        x_array,
    )

    if normalization <= 0.0:
        raise ValueError(
            "Quadrature density could not be normalized."
        )

    return np.asarray(
        probability_density / normalization,
        dtype=np.float64,
    )


def sample_from_density(
    x_values: RealVector,
    probability_density: RealVector,
    sample_count: int,
    rng: np.random.Generator,
) -> RealVector:
    """Draw approximate samples from a discretized density."""
    if sample_count <= 0:
        raise ValueError(
            "Sample count must be positive."
        )

    x_array = np.asarray(
        x_values,
        dtype=float,
    )
    probabilities = np.asarray(
        probability_density,
        dtype=float,
    )

    if x_array.ndim != 1 or probabilities.ndim != 1:
        raise ValueError(
            "Grid and probability density must be one-dimensional."
        )

    if x_array.shape != probabilities.shape:
        raise ValueError(
            "Grid and probability density must have the same shape."
        )

    if x_array.size < 2:
        raise ValueError(
            "The sampling grid must contain at least two points."
        )

    probability_sum = float(
        np.sum(probabilities)
    )

    if probability_sum <= 0.0:
        raise ValueError(
            "Probability density must have positive total weight."
        )

    probabilities = probabilities / probability_sum

    indices = rng.choice(
        len(x_array),
        size=sample_count,
        p=probabilities,
    )

    spacing = float(
        x_array[1] - x_array[0]
    )

    jitter = rng.uniform(
        low=-0.5 * spacing,
        high=0.5 * spacing,
        size=sample_count,
    )

    return np.asarray(
        x_array[indices] + jitter,
        dtype=np.float64,
    )


def sign_free_samples(
    quadrature_samples: RealVector,
) -> RealVector:
    """Convert ordinary outcomes x_phi into |x_phi|."""
    return np.abs(
        np.asarray(
            quadrature_samples,
            dtype=float,
        )
    )


__all__ = [
    "RealVector",
    "quadrature_probability_density",
    "quadrature_wavefunction",
    "sample_from_density",
    "sign_free_samples",
]
