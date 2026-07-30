from __future__ import annotations

import math

import numpy as np

from iqcore.states import (
    ComplexMatrix,
    QuantumStateArray,
    density_matrix,
)


def pure_loss_kraus_operators(
    transmissivity: float,
    cutoff: int,
) -> list[ComplexMatrix]:
    """
    Construct Kraus operators for a single-mode bosonic
    pure-loss channel.

    The channel transmissivity is denoted by eta, where

        0 <= eta <= 1.

    The l-th Kraus operator is

        A_l = sum_{n=l}^{cutoff-1}
              sqrt[C(n,l)]
              (1-eta)^(l/2)
              eta^((n-l)/2)
              |n-l><n|.
    """
    if not 0.0 <= transmissivity <= 1.0:
        raise ValueError(
            "Transmissivity must lie between 0 and 1."
        )

    if cutoff <= 0:
        raise ValueError(
            "Cutoff must be positive."
        )

    eta = float(transmissivity)
    loss_probability = 1.0 - eta
    kraus_operators: list[ComplexMatrix] = []

    for lost_photons in range(cutoff):
        operator = np.zeros(
            (cutoff, cutoff),
            dtype=np.complex128,
        )

        for input_photons in range(
            lost_photons,
            cutoff,
        ):
            output_photons = (
                input_photons - lost_photons
            )

            coefficient = np.sqrt(
                math.comb(
                    input_photons,
                    lost_photons,
                )
                * loss_probability**lost_photons
                * eta**output_photons
            )

            operator[
                output_photons,
                input_photons,
            ] = coefficient

        kraus_operators.append(operator)

    return kraus_operators


def pure_loss_channel(
    state: QuantumStateArray,
    transmissivity: float,
) -> ComplexMatrix:
    """
    Apply a single-mode bosonic pure-loss channel.

        E_eta(rho) = sum_l A_l rho A_l^dagger.

    A pure input may become mixed, so this function always
    returns a density matrix.
    """
    rho_input = density_matrix(state)
    cutoff = rho_input.shape[0]

    rho_output = np.zeros_like(
        rho_input,
        dtype=np.complex128,
    )

    for operator in pure_loss_kraus_operators(
        transmissivity=transmissivity,
        cutoff=cutoff,
    ):
        rho_output += (
            operator
            @ rho_input
            @ operator.conjugate().T
        )

    rho_output = 0.5 * (
        rho_output
        + rho_output.conjugate().T
    )

    trace = np.trace(rho_output)

    if np.isclose(abs(trace), 0.0):
        raise ValueError(
            "Output state has zero trace."
        )

    return np.asarray(
        rho_output / trace,
        dtype=np.complex128,
    )


__all__ = [
    "pure_loss_channel",
    "pure_loss_kraus_operators",
]
