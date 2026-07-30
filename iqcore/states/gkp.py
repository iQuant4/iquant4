from __future__ import annotations

import numpy as np

from iqcore.operators import (
    displacement_operator,
    squeezing_operator,
)

from ._types import ComplexVector


def approximate_gkp_state(
    delta: float,
    kappa: float,
    cutoff: int,
    logical_index: int = 0,
    dimension: int = 2,
    lattice_cutoff: int = 6,
) -> ComplexVector:
    """
    Construct an approximate square-lattice GKP state.

    The implemented state is

        |GKP_{j,Delta,kappa}> ∝
        sum_s exp[
            -pi kappa^2 (d s + j)^2 / d
        ]
        D[
            sqrt(pi/d) (d s + j)
        ]
        S(-ln Delta) |0>.
    """
    if not 0.0 < delta <= 1.0:
        raise ValueError(
            "Delta must lie in the interval (0, 1]."
        )

    if kappa <= 0.0:
        raise ValueError(
            "Kappa must be positive."
        )

    if cutoff <= 0:
        raise ValueError(
            "Cutoff must be positive."
        )

    if dimension < 2:
        raise ValueError(
            "Dimension must be at least 2."
        )

    if not 0 <= logical_index < dimension:
        raise ValueError(
            "Logical index must satisfy 0 <= j < d."
        )

    if lattice_cutoff < 0:
        raise ValueError(
            "Lattice cutoff cannot be negative."
        )

    vacuum = np.zeros(
        cutoff,
        dtype=np.complex128,
    )
    vacuum[0] = 1.0

    squeezing_parameter = -np.log(delta)

    squeezed_vacuum = (
        squeezing_operator(
            xi=squeezing_parameter,
            cutoff=cutoff,
        )
        @ vacuum
    )

    state = np.zeros(
        cutoff,
        dtype=np.complex128,
    )

    for lattice_index in range(
        -lattice_cutoff,
        lattice_cutoff + 1,
    ):
        integer_coordinate = (
            dimension * lattice_index
            + logical_index
        )

        envelope_weight = np.exp(
            -np.pi
            * kappa**2
            * integer_coordinate**2
            / dimension
        )

        displacement_amplitude = (
            np.sqrt(np.pi / dimension)
            * integer_coordinate
        )

        displaced_peak = (
            displacement_operator(
                alpha=displacement_amplitude,
                cutoff=cutoff,
            )
            @ squeezed_vacuum
        )

        state += (
            envelope_weight
            * displaced_peak
        )

    norm = np.linalg.norm(state)

    if norm == 0.0:
        raise ValueError(
            "The approximate GKP state has zero norm."
        )

    return state / norm


__all__ = ["approximate_gkp_state"]
