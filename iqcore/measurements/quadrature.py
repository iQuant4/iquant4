from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from numpy.typing import ArrayLike, NDArray
from iqcore.operators import annihilation_operator
from iqcore.states import (
    QuantumStateArray,
    density_matrix,
)


RealArray = NDArray[np.float64]
ComplexArray = NDArray[np.complex128]


@dataclass(frozen=True)
class QuadratureStatistics:
    """
    Statistical moments of a rotated quadrature measurement.

    The quadrature convention is

        X_theta =
            (
                exp(-i theta) a
                + exp(i theta) a_dagger
            ) / sqrt(2).

    With this convention, the vacuum variance is 1/2.
    """

    angle: float
    mean: float
    second_moment: float
    variance: float
    standard_deviation: float


def _state_dimension(
    state: QuantumStateArray,
) -> int:
    """
    Return the Hilbert-space dimension of a ket or density
    matrix.
    """
    state_array = np.asarray(
        state,
        dtype=np.complex128,
    )

    if state_array.ndim == 1:
        return int(state_array.size)

    if (
        state_array.ndim == 2
        and state_array.shape[0]
        == state_array.shape[1]
    ):
        return int(state_array.shape[0])

    raise ValueError(
        "State must be a ket or a square density matrix."
    )


def quadrature_operator(
    cutoff: int,
    angle: float = 0.0,
) -> ComplexArray:
    """
    Construct a rotated quadrature operator.

    The operator is

        X_theta =
            (
                exp(-i theta) a
                + exp(i theta) a_dagger
            ) / sqrt(2).

    Parameters
    ----------
    cutoff:
        Fock-space truncation dimension.

    angle:
        Local-oscillator phase in radians.

    Returns
    -------
    numpy.ndarray
        Quadrature operator with shape ``(cutoff, cutoff)``.
    """
    if cutoff <= 0:
        raise ValueError(
            "Cutoff must be positive."
        )

    annihilation = annihilation_operator(
        cutoff=cutoff
    )

    creation = annihilation.conjugate().T

    operator = (
        np.exp(-1j * angle) * annihilation
        + np.exp(1j * angle) * creation
    ) / np.sqrt(2.0)

    return np.asarray(
        operator,
        dtype=np.complex128,
    )


def position_quadrature_operator(
    cutoff: int,
) -> ComplexArray:
    """
    Construct the position-like quadrature

        X = (a + a_dagger) / sqrt(2).
    """
    return quadrature_operator(
        cutoff=cutoff,
        angle=0.0,
    )


def momentum_quadrature_operator(
    cutoff: int,
) -> ComplexArray:
    """
    Construct the momentum-like quadrature

        P = (a - a_dagger) / (i sqrt(2)).
    """
    return quadrature_operator(
        cutoff=cutoff,
        angle=np.pi / 2.0,
    )


def expectation_value(
    state: QuantumStateArray,
    operator: ComplexArray,
) -> complex:
    """
    Calculate the expectation value of an operator.
    """
    rho = density_matrix(state)

    operator_array = np.asarray(
        operator,
        dtype=np.complex128,
    )

    if operator_array.shape != rho.shape:
        raise ValueError(
            "Operator and state dimensions are incompatible."
        )

    return complex(
        np.trace(
            rho @ operator_array
        )
    )


def quadrature_statistics(
    state: QuantumStateArray,
    angle: float = 0.0,
) -> QuadratureStatistics:
    """
    Calculate the mean and variance of a rotated quadrature.

    Parameters
    ----------
    state:
        Ket or density matrix.

    angle:
        Quadrature angle in radians.

    Returns
    -------
    QuadratureStatistics
        Mean, second moment, variance, and standard deviation.
    """
    cutoff = _state_dimension(state)

    quadrature = quadrature_operator(
        cutoff=cutoff,
        angle=angle,
    )

    quadrature_squared = (
        quadrature @ quadrature
    )

    mean_complex = expectation_value(
        state,
        quadrature,
    )

    second_moment_complex = expectation_value(
        state,
        quadrature_squared,
    )

    mean = float(
        np.real_if_close(mean_complex).real
    )

    second_moment = float(
        np.real_if_close(
            second_moment_complex
        ).real
    )

    variance = second_moment - mean**2

    # Suppress tiny negative values produced by floating-point
    # roundoff.
    if variance < 0.0 and np.isclose(
        variance,
        0.0,
        atol=1e-12,
    ):
        variance = 0.0

    if variance < 0.0:
        raise ValueError(
            "Calculated quadrature variance is negative. "
            "Increase the Fock cutoff or validate the state."
        )

    return QuadratureStatistics(
        angle=float(angle),
        mean=mean,
        second_moment=second_moment,
        variance=float(variance),
        standard_deviation=float(
            np.sqrt(variance)
        ),
    )


def _harmonic_oscillator_wavefunctions(
    x_values: ArrayLike,
    cutoff: int,
) -> RealArray:
    """
    Calculate normalized Fock-state quadrature wavefunctions.

    The returned array contains

        wavefunctions[n, j] = <x_j|n>.

    A stable three-term recurrence is used instead of directly
    evaluating large Hermite polynomials.
    """
    if cutoff <= 0:
        raise ValueError(
            "Cutoff must be positive."
        )

    x_array = np.asarray(
        x_values,
        dtype=np.float64,
    )

    if x_array.ndim != 1:
        raise ValueError(
            "Quadrature grid must be one-dimensional."
        )

    if x_array.size < 2:
        raise ValueError(
            "Quadrature grid must contain at least two points."
        )

    wavefunctions = np.zeros(
        (cutoff, x_array.size),
        dtype=np.float64,
    )

    wavefunctions[0] = (
        np.pi ** (-0.25)
        * np.exp(-0.5 * x_array**2)
    )

    if cutoff == 1:
        return wavefunctions

    wavefunctions[1] = (
        np.sqrt(2.0)
        * x_array
        * wavefunctions[0]
    )

    for photon_number in range(
        1,
        cutoff - 1,
    ):
        wavefunctions[photon_number + 1] = (
            np.sqrt(
                2.0
                / (photon_number + 1)
            )
            * x_array
            * wavefunctions[photon_number]
            - np.sqrt(
                photon_number
                / (photon_number + 1)
            )
            * wavefunctions[photon_number - 1]
        )

    return wavefunctions


def fock_quadrature_wavefunctions(
    x_values: ArrayLike,
    cutoff: int,
    angle: float = 0.0,
) -> ComplexArray:
    """
    Return rotated Fock-basis quadrature wavefunctions.

    The array follows

        wavefunctions[n, j] = <x_theta,j|n>.

    Rotation introduces the phase

        <x_theta|n>
            = exp(-i n theta) <x|n>.
    """
    base_wavefunctions = (
        _harmonic_oscillator_wavefunctions(
            x_values=x_values,
            cutoff=cutoff,
        )
    )

    photon_numbers = np.arange(
        cutoff,
        dtype=np.float64,
    )

    phases = np.exp(
        -1j * photon_numbers * angle
    )

    return np.asarray(
        phases[:, np.newaxis]
        * base_wavefunctions,
        dtype=np.complex128,
    )


def quadrature_probability_density(
    state: QuantumStateArray,
    x_values: ArrayLike,
    angle: float = 0.0,
    *,
    normalize: bool = True,
) -> RealArray:
    """
    Calculate a continuous quadrature probability density.

    For a ket,

        p(x_theta)
            = |<x_theta|psi>|^2.

    For a density matrix,

        p(x_theta)
            = <x_theta|rho|x_theta>.

    Parameters
    ----------
    state:
        Ket or density matrix.

    x_values:
        One-dimensional quadrature grid.

    angle:
        Local-oscillator phase in radians.

    normalize:
        Numerically normalize the density over the supplied
        grid. This should usually remain ``True``.

    Returns
    -------
    numpy.ndarray
        Probability-density values on the supplied grid.
    """
    x_array = np.asarray(
        x_values,
        dtype=np.float64,
    )

    if x_array.ndim != 1:
        raise ValueError(
            "Quadrature grid must be one-dimensional."
        )

    if x_array.size < 2:
        raise ValueError(
            "Quadrature grid must contain at least two points."
        )

    if np.any(
        np.diff(x_array) <= 0.0
    ):
        raise ValueError(
            "Quadrature-grid values must be strictly "
            "increasing."
        )

    cutoff = _state_dimension(state)

    basis_wavefunctions = (
        fock_quadrature_wavefunctions(
            x_values=x_array,
            cutoff=cutoff,
            angle=angle,
        )
    )

    state_array = np.asarray(
        state,
        dtype=np.complex128,
    )

    if state_array.ndim == 1:
        amplitude = (
            basis_wavefunctions.T
            @ state_array
        )

        probability_density = (
            np.abs(amplitude) ** 2
        )

    else:
        rho = density_matrix(state)

        probability_density = np.einsum(
            "mx,mn,nx->x",
            basis_wavefunctions,
            rho,
            basis_wavefunctions.conjugate(),
            optimize=True,
        ).real

    # Tiny negative values can appear from floating-point
    # evaluation of density matrices.
    probability_density = np.where(
        probability_density < 0.0,
        np.maximum(
            probability_density,
            0.0,
        ),
        probability_density,
    )

    if normalize:
        integral = float(
            np.trapezoid(
                probability_density,
                x_array,
            )
        )

        if integral <= 0.0:
            raise ValueError(
                "Quadrature density has zero numerical "
                "normalization."
            )

        probability_density = (
            probability_density / integral
        )

    return np.asarray(
        probability_density,
        dtype=np.float64,
    )


def quadrature_distribution_normalization(
    x_values: ArrayLike,
    probability_density: ArrayLike,
) -> float:
    """
    Numerically integrate a quadrature probability density.
    """
    x_array = np.asarray(
        x_values,
        dtype=np.float64,
    )

    density_array = np.asarray(
        probability_density,
        dtype=np.float64,
    )

    if x_array.shape != density_array.shape:
        raise ValueError(
            "Grid and probability density must have the same "
            "shape."
        )

    return float(
        np.trapezoid(
            density_array,
            x_array,
        )
    )


def distribution_statistics(
    x_values: ArrayLike,
    probability_density: ArrayLike,
) -> tuple[float, float]:
    """
    Calculate the mean and variance from a numerical density.
    """
    x_array = np.asarray(
        x_values,
        dtype=np.float64,
    )

    density_array = np.asarray(
        probability_density,
        dtype=np.float64,
    )

    if x_array.shape != density_array.shape:
        raise ValueError(
            "Grid and probability density must have the same "
            "shape."
        )

    normalization = float(
        np.trapezoid(
            density_array,
            x_array,
        )
    )

    if normalization <= 0.0:
        raise ValueError(
            "Probability density has zero normalization."
        )

    normalized_density = (
        density_array / normalization
    )

    mean = float(
        np.trapezoid(
            x_array * normalized_density,
            x_array,
        )
    )

    second_moment = float(
        np.trapezoid(
            x_array**2 * normalized_density,
            x_array,
        )
    )

    variance = second_moment - mean**2

    if variance < 0.0 and np.isclose(
        variance,
        0.0,
        atol=1e-12,
    ):
        variance = 0.0

    return mean, float(variance)


def sample_quadrature(
    state: QuantumStateArray,
    number_of_samples: int,
    angle: float = 0.0,
    *,
    x_min: float = -8.0,
    x_max: float = 8.0,
    number_of_grid_points: int = 4001,
    seed: int | None = None,
) -> RealArray:
    """
    Draw numerical samples from a quadrature distribution.

    Sampling uses a discretized cumulative distribution
    constructed from the continuous quadrature density.

    Parameters
    ----------
    state:
        Ket or density matrix.

    number_of_samples:
        Number of measurement outcomes.

    angle:
        Local-oscillator phase.

    x_min, x_max:
        Numerical quadrature range.

    number_of_grid_points:
        Resolution of the numerical distribution.

    seed:
        Random-number-generator seed.

    Returns
    -------
    numpy.ndarray
        Simulated homodyne outcomes.
    """
    if number_of_samples <= 0:
        raise ValueError(
            "Number of samples must be positive."
        )

    if x_max <= x_min:
        raise ValueError(
            "x_max must be greater than x_min."
        )

    if number_of_grid_points < 101:
        raise ValueError(
            "Use at least 101 quadrature-grid points."
        )

    x_values = np.linspace(
        x_min,
        x_max,
        number_of_grid_points,
        dtype=np.float64,
    )

    probability_density = (
        quadrature_probability_density(
            state=state,
            x_values=x_values,
            angle=angle,
            normalize=True,
        )
    )

    grid_spacing = np.diff(
        x_values
    )

    cumulative_probability = np.zeros_like(
        x_values
    )

    cumulative_probability[1:] = np.cumsum(
        0.5
        * (
            probability_density[:-1]
            + probability_density[1:]
        )
        * grid_spacing
    )

    cumulative_probability /= (
        cumulative_probability[-1]
    )

    # Ensure a strictly valid final CDF value.
    cumulative_probability[-1] = 1.0

    rng = np.random.default_rng(seed)

    uniform_samples = rng.random(
        number_of_samples
    )

    samples = np.interp(
        uniform_samples,
        cumulative_probability,
        x_values,
    )

    return np.asarray(
        samples,
        dtype=np.float64,
    )


def coherent_quadrature_parameters(
    alpha: complex,
    angle: float = 0.0,
    efficiency: float = 1.0,
    excess_noise_variance: float = 0.0,
) -> tuple[float, float]:
    """
    Return the analytical mean and variance for homodyne
    detection of a coherent state.

    The mean is

        sqrt(2 eta) Re[alpha exp(-i theta)],

    and the variance is

        1/2 + excess_noise_variance.

    This follows the same convention as the existing
    ``HomodyneReceiver``.
    """
    if not 0.0 <= efficiency <= 1.0:
        raise ValueError(
            "Efficiency must be between 0 and 1."
        )

    if excess_noise_variance < 0.0:
        raise ValueError(
            "Excess-noise variance cannot be negative."
        )

    rotated_alpha = (
        alpha * np.exp(-1j * angle)
    )

    mean = float(
        np.sqrt(2.0 * efficiency)
        * np.real(rotated_alpha)
    )

    variance = float(
        0.5 + excess_noise_variance
    )

    return mean, variance


__all__ = [
    "ComplexArray",
    "QuadratureStatistics",
    "RealArray",
    "coherent_quadrature_parameters",
    "distribution_statistics",
    "expectation_value",
    "fock_quadrature_wavefunctions",
    "momentum_quadrature_operator",
    "position_quadrature_operator",
    "quadrature_distribution_normalization",
    "quadrature_operator",
    "quadrature_probability_density",
    "quadrature_statistics",
    "sample_quadrature",
]
