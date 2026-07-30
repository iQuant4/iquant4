from __future__ import annotations

import math

import numpy as np
from numpy.typing import NDArray
from scipy.special import eval_hermite

from iqcore.states import (
    ComplexMatrix,
    ComplexVector,
)


RealVector = NDArray[np.float64]


def quadrature_bra_coefficients(
    x: float,
    phase: float,
    cutoff: int,
) -> ComplexVector:
    """
    Return the coefficients <x_phi|n> for

        n = 0, ..., cutoff - 1.

    The quadrature convention is

        x_phi = (
            a exp(-i phi)
            + a^dagger exp(i phi)
        ) / sqrt(2).
    """
    if cutoff <= 0:
        raise ValueError(
            "Cutoff must be positive."
        )

    coefficients = np.zeros(
        cutoff,
        dtype=np.complex128,
    )

    gaussian_factor = (
        np.pi ** (-0.25)
        * np.exp(-0.5 * x**2)
    )

    for n in range(cutoff):
        normalization = math.sqrt(
            (2.0**n) * math.factorial(n)
        )

        coefficients[n] = (
            gaussian_factor
            * eval_hermite(n, x)
            / normalization
            * np.exp(-1j * n * phase)
        )

    return coefficients

def sign_free_povm_density(
    x_absolute: float,
    phase: float,
    cutoff: int,
) -> ComplexMatrix:
    """
    Construct the ideal sign-free quadrature POVM density

        E(|x|, phi)
        =
        |x_phi><x_phi|
        +
        |-x_phi><-x_phi|.

    The outcome x_absolute must be nonnegative.
    """
    if x_absolute < 0.0:
        raise ValueError(
            "Sign-free quadrature must be nonnegative."
        )

    bra_positive = quadrature_bra_coefficients(
        x=x_absolute,
        phase=phase,
        cutoff=cutoff,
    )

    bra_negative = quadrature_bra_coefficients(
        x=-x_absolute,
        phase=phase,
        cutoff=cutoff,
    )

    projector_positive = np.outer(
        np.conjugate(bra_positive),
        bra_positive,
    )

    projector_negative = np.outer(
        np.conjugate(bra_negative),
        bra_negative,
    )

    operator = (
        projector_positive
        + projector_negative
    )

    # Remove insignificant numerical non-Hermitian errors.
    operator = (
        operator
        + operator.conjugate().T
    ) / 2.0

    return operator

def integrate_sign_free_povm_bin(
    lower_edge: float,
    upper_edge: float,
    phase: float,
    cutoff: int,
    integration_points: int = 9,
) -> ComplexMatrix:
    """
    Integrate the sign-free POVM density over one
    histogram bin.
    """
    if lower_edge < 0.0:
        raise ValueError(
            "Bin lower edge cannot be negative."
        )

    if upper_edge <= lower_edge:
        raise ValueError(
            "Upper edge must exceed the lower edge."
        )

    if integration_points < 2:
        raise ValueError(
            "At least two integration points are required."
        )

    x_grid = np.linspace(
        lower_edge,
        upper_edge,
        integration_points,
    )

    povm_values = np.stack(
        [
            sign_free_povm_density(
                x_absolute=float(x),
                phase=phase,
                cutoff=cutoff,
            )
            for x in x_grid
        ],
        axis=0,
    )

    integrated_operator = np.trapezoid(
        povm_values,
        x_grid,
        axis=0,
    )

    integrated_operator = (
        integrated_operator
        + integrated_operator.conjugate().T
    ) / 2.0

    return np.asarray(
        integrated_operator,
        dtype=np.complex128,
    )

def build_measurement_operators(
    phases: RealVector,
    bin_edges: RealVector,
    cutoff: int,
    integration_points: int = 9,
) -> list[ComplexMatrix]:
    """
    Build one integrated POVM operator for every
    phase-and-bin combination.

    The ordering is:

        phase 0, all bins
        phase 1, all bins
        ...
    """
    phases = np.asarray(
        phases,
        dtype=float,
    )

    bin_edges = np.asarray(
        bin_edges,
        dtype=float,
    )

    if phases.ndim != 1:
        raise ValueError(
            "Phases must be a one-dimensional array."
        )

    if bin_edges.ndim != 1:
        raise ValueError(
            "Bin edges must be a one-dimensional array."
        )

    if len(phases) == 0:
        raise ValueError(
            "At least one measurement phase is required."
        )

    if len(bin_edges) < 2:
        raise ValueError(
            "At least two bin edges are required."
        )

    if np.any(np.diff(bin_edges) <= 0.0):
        raise ValueError(
            "Histogram bin edges must be increasing."
        )

    if bin_edges[0] < 0.0:
        raise ValueError(
            "Sign-free histogram bins must start at "
            "a nonnegative value."
        )

    operators: list[ComplexMatrix] = []

    for phase in phases:
        for bin_index in range(
            len(bin_edges) - 1
        ):
            operator = integrate_sign_free_povm_bin(
                lower_edge=float(
                    bin_edges[bin_index]
                ),
                upper_edge=float(
                    bin_edges[bin_index + 1]
                ),
                phase=float(phase),
                cutoff=cutoff,
                integration_points=integration_points,
            )

            operators.append(operator)

    return operators

def histogram_probabilities(
    samples_by_phase: list[RealVector],
    bin_edges: RealVector,
) -> RealVector:
    """
    Convert sign-free samples into a flattened vector
    of empirical bin probabilities.
    """
    bin_edges = np.asarray(
        bin_edges,
        dtype=float,
    )

    if len(samples_by_phase) == 0:
        raise ValueError(
            "At least one phase dataset is required."
        )

    probabilities: list[float] = []

    for phase_index, samples in enumerate(
        samples_by_phase
    ):
        samples = np.asarray(
            samples,
            dtype=float,
        )

        if samples.ndim != 1:
            raise ValueError(
                f"Samples for phase {phase_index} must "
                "be one-dimensional."
            )

        if np.any(samples < 0.0):
            raise ValueError(
                "Sign-free samples cannot be negative."
            )

        counts, _ = np.histogram(
            samples,
            bins=bin_edges,
        )

        total_count = int(
            np.sum(counts)
        )

        if total_count == 0:
            raise ValueError(
                f"No samples for phase {phase_index} "
                "fell inside the histogram range."
            )

        phase_probabilities = (
            counts.astype(float)
            / total_count
        )

        probabilities.extend(
            phase_probabilities.tolist()
        )

    return np.asarray(
        probabilities,
        dtype=float,
    )


__all__ = [
    "RealVector",
    "build_measurement_operators",
    "histogram_probabilities",
    "integrate_sign_free_povm_bin",
    "quadrature_bra_coefficients",
    "sign_free_povm_density",
]
