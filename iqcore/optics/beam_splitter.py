from __future__ import annotations

from collections.abc import Sequence

import numpy as np
from scipy.linalg import expm

from iqcore.states import (
    ComplexMatrix,
    ComplexVector,
    Dimensions,
    QuantumStateArray,
    density_matrix,
    is_ket,
    normalize_ket,
    validate_dimensions,
    validate_state_dimensions,
)

from iqcore.operators import (
    annihilation_operator,
)


def beam_splitter_angle(
    transmissivity: float,
) -> float:
    """
    Convert power transmissivity into a beam-splitter angle.

    iquant4comm uses

        transmissivity = cos(theta)^2.

    Therefore,

        theta = arccos(sqrt(transmissivity)).

    Parameters
    ----------
    transmissivity:
        Beam-splitter power transmissivity between zero and
        one.

    Returns
    -------
    float
        Beam-splitter mixing angle in radians.
    """
    if not 0.0 <= transmissivity <= 1.0:
        raise ValueError(
            "Transmissivity must lie between 0 and 1."
        )

    return float(
        np.arccos(
            np.sqrt(transmissivity)
        )
    )


def beam_splitter_transmissivity(
    angle: float,
) -> float:
    """
    Convert a beam-splitter angle into power transmissivity.

    The convention is

        transmissivity = cos(theta)^2.
    """
    return float(
        np.cos(angle) ** 2
    )


def two_mode_annihilation_operators(
    dimensions: Sequence[int],
) -> tuple[
    ComplexMatrix,
    ComplexMatrix,
]:
    """
    Construct annihilation operators for a two-mode system.

    For subsystem dimensions ``(d_a, d_b)``, this returns

        a = a_single tensor I_b,

        b = I_a tensor b_single.

    Parameters
    ----------
    dimensions:
        Two-mode Hilbert-space dimensions.

    Returns
    -------
    tuple
        Composite annihilation operators for modes A and B.
    """
    validated_dimensions = validate_dimensions(
        dimensions
    )

    if len(validated_dimensions) != 2:
        raise ValueError(
            "A beam splitter requires exactly two modes."
        )

    dimension_a, dimension_b = (
        validated_dimensions
    )

    annihilation_a = annihilation_operator(
        cutoff=dimension_a
    )

    annihilation_b = annihilation_operator(
        cutoff=dimension_b
    )

    identity_a = np.eye(
        dimension_a,
        dtype=np.complex128,
    )

    identity_b = np.eye(
        dimension_b,
        dtype=np.complex128,
    )

    composite_a = np.kron(
        annihilation_a,
        identity_b,
    )

    composite_b = np.kron(
        identity_a,
        annihilation_b,
    )

    return (
        np.asarray(
            composite_a,
            dtype=np.complex128,
        ),
        np.asarray(
            composite_b,
            dtype=np.complex128,
        ),
    )


def beam_splitter_unitary(
    dimensions: Sequence[int],
    *,
    angle: float | None = None,
    transmissivity: float | None = None,
    phase: float = 0.0,
) -> ComplexMatrix:
    """
    Construct a two-mode beam-splitter unitary.

    Exactly one of ``angle`` or ``transmissivity`` must be
    supplied.

    The unitary is

        U_BS =
        exp[
            theta (
                exp(i phi) a^dagger b
                - exp(-i phi) a b^dagger
            )
        ].

    For ``phase=0``, the corresponding mode transformation is

        U_BS^dagger a U_BS
            = a cos(theta) + b sin(theta),

        U_BS^dagger b U_BS
            = b cos(theta) - a sin(theta).

    The power transmissivity is

        eta = cos(theta)^2.

    Parameters
    ----------
    dimensions:
        Dimensions of the two optical modes.

    angle:
        Beam-splitter mixing angle in radians.

    transmissivity:
        Power transmissivity between zero and one.

    phase:
        Relative beam-splitter phase in radians.

    Returns
    -------
    numpy.ndarray
        Two-mode unitary matrix.
    """
    validated_dimensions = validate_dimensions(
        dimensions
    )

    if len(validated_dimensions) != 2:
        raise ValueError(
            "A beam splitter requires exactly two modes."
        )

    if (
        angle is None
        and transmissivity is None
    ):
        raise ValueError(
            "Specify either angle or transmissivity."
        )

    if (
        angle is not None
        and transmissivity is not None
    ):
        raise ValueError(
            "Specify angle or transmissivity, not both."
        )

    if transmissivity is not None:
        mixing_angle = beam_splitter_angle(
            transmissivity
        )
    else:
        mixing_angle = float(angle)

    operator_a, operator_b = (
        two_mode_annihilation_operators(
            validated_dimensions
        )
    )

    operator_a_dagger = (
        operator_a.conjugate().T
    )

    operator_b_dagger = (
        operator_b.conjugate().T
    )

    generator = mixing_angle * (
        np.exp(1j * phase)
        * operator_a_dagger
        @ operator_b
        - np.exp(-1j * phase)
        * operator_a
        @ operator_b_dagger
    )

    unitary = expm(generator)

    return np.asarray(
        unitary,
        dtype=np.complex128,
    )


def apply_beam_splitter(
    state: QuantumStateArray,
    dimensions: Sequence[int],
    *,
    angle: float | None = None,
    transmissivity: float | None = None,
    phase: float = 0.0,
) -> QuantumStateArray:
    """
    Apply a beam splitter to a two-mode quantum state.

    Ket inputs produce ket outputs. Density-matrix inputs
    produce density-matrix outputs.

    Parameters
    ----------
    state:
        Two-mode ket or density matrix.

    dimensions:
        Dimensions of the two modes.

    angle:
        Beam-splitter angle in radians.

    transmissivity:
        Power transmissivity between zero and one.

    phase:
        Relative beam-splitter phase.

    Returns
    -------
    numpy.ndarray
        Transformed ket or density matrix.
    """
    validated_dimensions = (
        validate_state_dimensions(
            state,
            dimensions,
        )
    )

    if len(validated_dimensions) != 2:
        raise ValueError(
            "A beam splitter requires exactly two modes."
        )

    unitary = beam_splitter_unitary(
        validated_dimensions,
        angle=angle,
        transmissivity=transmissivity,
        phase=phase,
    )

    if is_ket(state):
        input_ket = normalize_ket(state)

        output_ket = (
            unitary
            @ input_ket
        )

        return normalize_ket(
            output_ket
        )

    rho_input = density_matrix(state)

    rho_output = (
        unitary
        @ rho_input
        @ unitary.conjugate().T
    )

    rho_output = 0.5 * (
        rho_output
        + rho_output.conjugate().T
    )

    trace = np.trace(rho_output)

    if np.isclose(
        abs(trace),
        0.0,
    ):
        raise ValueError(
            "Beam-splitter output has zero trace."
        )

    return np.asarray(
        rho_output / trace,
        dtype=np.complex128,
    )


def unitary_error(
    unitary: ComplexMatrix,
) -> float:
    """
    Calculate the error in the unitarity condition.

    The returned value is

        ||U^dagger U - I||.
    """
    unitary_array = np.asarray(
        unitary,
        dtype=np.complex128,
    )

    if (
        unitary_array.ndim != 2
        or unitary_array.shape[0]
        != unitary_array.shape[1]
    ):
        raise ValueError(
            "Unitary candidate must be square."
        )

    identity = np.eye(
        unitary_array.shape[0],
        dtype=np.complex128,
    )

    return float(
        np.linalg.norm(
            unitary_array.conjugate().T
            @ unitary_array
            - identity
        )
    )


def two_mode_number_operators(
    dimensions: Sequence[int],
) -> tuple[
    ComplexMatrix,
    ComplexMatrix,
]:
    """
    Construct photon-number operators for two modes.
    """
    operator_a, operator_b = (
        two_mode_annihilation_operators(
            dimensions
        )
    )

    number_a = (
        operator_a.conjugate().T
        @ operator_a
    )

    number_b = (
        operator_b.conjugate().T
        @ operator_b
    )

    return number_a, number_b


def mean_mode_photon_numbers(
    state: QuantumStateArray,
    dimensions: Sequence[int],
) -> tuple[float, float]:
    """
    Calculate the mean photon number in each output mode.
    """
    validated_dimensions = (
        validate_state_dimensions(
            state,
            dimensions,
        )
    )

    rho = density_matrix(state)

    number_a, number_b = (
        two_mode_number_operators(
            validated_dimensions
        )
    )

    mean_a = np.real(
        np.trace(
            rho @ number_a
        )
    )

    mean_b = np.real(
        np.trace(
            rho @ number_b
        )
    )

    return (
        float(mean_a),
        float(mean_b),
    )


def total_photon_number_error(
    input_state: QuantumStateArray,
    output_state: QuantumStateArray,
    dimensions: Sequence[int],
) -> float:
    """
    Calculate the beam-splitter photon-number conservation
    error.
    """
    input_a, input_b = (
        mean_mode_photon_numbers(
            input_state,
            dimensions,
        )
    )

    output_a, output_b = (
        mean_mode_photon_numbers(
            output_state,
            dimensions,
        )
    )

    return float(
        abs(
            (output_a + output_b)
            - (input_a + input_b)
        )
    )