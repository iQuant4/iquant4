from __future__ import annotations

from collections.abc import Sequence
from typing import TypeAlias

import numpy as np
from numpy.typing import NDArray

from ._types import (
    ComplexMatrix,
    ComplexVector,
    QuantumStateArray,
)
from .validation import (
    density_matrix,
    is_ket,
    normalize_ket,
)


Dimensions: TypeAlias = tuple[int, ...]


def validate_dimensions(
    dimensions: Sequence[int],
) -> Dimensions:
    """
    Validate a collection of subsystem dimensions.

    Parameters
    ----------
    dimensions:
        Hilbert-space dimensions of the individual modes.

    Returns
    -------
    tuple[int, ...]
        Validated dimensions.

    Raises
    ------
    ValueError
        If no dimensions are supplied or any dimension is
        nonpositive.
    """
    validated_dimensions = tuple(
        int(dimension)
        for dimension in dimensions
    )

    if len(validated_dimensions) == 0:
        raise ValueError(
            "At least one subsystem dimension is required."
        )

    if any(
        dimension <= 0
        for dimension in validated_dimensions
    ):
        raise ValueError(
            "All subsystem dimensions must be positive."
        )

    return validated_dimensions


def total_dimension(
    dimensions: Sequence[int],
) -> int:
    """
    Return the total Hilbert-space dimension.

    For subsystem dimensions

        (d_0, d_1, ..., d_{M-1}),

    the total dimension is

        D = product_k d_k.
    """
    validated_dimensions = validate_dimensions(
        dimensions
    )

    return int(
        np.prod(
            validated_dimensions,
            dtype=np.int64,
        )
    )


def number_of_modes(
    dimensions: Sequence[int],
) -> int:
    """
    Return the number of subsystems or optical modes.
    """
    return len(
        validate_dimensions(dimensions)
    )


def mode_dimension(
    dimensions: Sequence[int],
    mode: int,
) -> int:
    """
    Return the Hilbert-space dimension of one mode.

    Parameters
    ----------
    dimensions:
        Dimensions of all modes.

    mode:
        Zero-based mode index.
    """
    validated_dimensions = validate_dimensions(
        dimensions
    )

    if not 0 <= mode < len(validated_dimensions):
        raise ValueError(
            "Mode index is outside the valid range."
        )

    return validated_dimensions[mode]


def validate_state_dimensions(
    state: QuantumStateArray,
    dimensions: Sequence[int],
) -> Dimensions:
    """
    Verify that a state is compatible with subsystem dimensions.

    Parameters
    ----------
    state:
        Ket or density matrix.

    dimensions:
        Subsystem dimensions.

    Returns
    -------
    tuple[int, ...]
        Validated dimensions.
    """
    validated_dimensions = validate_dimensions(
        dimensions
    )

    expected_dimension = total_dimension(
        validated_dimensions
    )

    state_array = np.asarray(
        state,
        dtype=np.complex128,
    )

    if state_array.ndim == 1:
        actual_dimension = state_array.size

    elif state_array.ndim == 2:
        rows, columns = state_array.shape

        if rows != columns:
            raise ValueError(
                "Density matrix must be square."
            )

        actual_dimension = rows

    else:
        raise ValueError(
            "State must be a ket or density matrix."
        )

    if actual_dimension != expected_dimension:
        raise ValueError(
            "State dimension is incompatible with subsystem "
            f"dimensions. Expected {expected_dimension}, "
            f"received {actual_dimension}."
        )

    return validated_dimensions


def tensor_product(
    *states: QuantumStateArray,
) -> QuantumStateArray:
    """
    Compute the tensor product of quantum states.

    If every input is a ket, the result is a ket.

    If one or more inputs are density matrices, all inputs are
    converted to density matrices and the result is a density
    matrix.

    Examples
    --------
    For two kets,

        |psi_AB> = |psi_A> tensor |psi_B>.

    For density matrices,

        rho_AB = rho_A tensor rho_B.

    Parameters
    ----------
    *states:
        Two or more state vectors or density matrices.

    Returns
    -------
    numpy.ndarray
        Composite ket or density matrix.
    """
    if len(states) < 2:
        raise ValueError(
            "At least two quantum states are required."
        )

    all_inputs_are_kets = all(
        is_ket(state)
        for state in states
    )

    if all_inputs_are_kets:
        result = normalize_ket(
            states[0]
        )

        for state in states[1:]:
            result = np.kron(
                result,
                normalize_ket(state),
            )

        return np.asarray(
            result,
            dtype=np.complex128,
        )

    result_matrix = density_matrix(
        states[0]
    )

    for state in states[1:]:
        result_matrix = np.kron(
            result_matrix,
            density_matrix(state),
        )

    return np.asarray(
        result_matrix,
        dtype=np.complex128,
    )


def density_tensor_product(
    *states: QuantumStateArray,
) -> ComplexMatrix:
    """
    Compute a tensor product and always return a density matrix.

    Ket inputs are converted according to

        rho = |psi><psi|.
    """
    if len(states) < 2:
        raise ValueError(
            "At least two quantum states are required."
        )

    result = density_matrix(
        states[0]
    )

    for state in states[1:]:
        result = np.kron(
            result,
            density_matrix(state),
        )

    return np.asarray(
        result,
        dtype=np.complex128,
    )


def basis_index(
    occupations: Sequence[int],
    dimensions: Sequence[int],
) -> int:
    """
    Convert multimode basis occupations to a flat index.

    iquant4comm uses NumPy tensor-product ordering. For dimensions

        (d_0, d_1, ..., d_{M-1}),

    the rightmost mode index varies fastest.

    For two equal-cutoff modes,

        index = n_0 * cutoff + n_1.

    Parameters
    ----------
    occupations:
        Basis index of each mode.

    dimensions:
        Dimension of each mode.

    Returns
    -------
    int
        Flattened basis index.
    """
    validated_dimensions = validate_dimensions(
        dimensions
    )

    occupation_tuple = tuple(
        int(occupation)
        for occupation in occupations
    )

    if len(occupation_tuple) != len(
        validated_dimensions
    ):
        raise ValueError(
            "One occupation number is required for each mode."
        )

    for occupation, dimension in zip(
        occupation_tuple,
        validated_dimensions,
        strict=True,
    ):
        if not 0 <= occupation < dimension:
            raise ValueError(
                "Occupation index lies outside its mode "
                "dimension."
            )

    return int(
        np.ravel_multi_index(
            occupation_tuple,
            validated_dimensions,
            order="C",
        )
    )


def basis_occupations(
    index: int,
    dimensions: Sequence[int],
) -> tuple[int, ...]:
    """
    Convert a flat basis index to multimode occupations.
    """
    validated_dimensions = validate_dimensions(
        dimensions
    )

    dimension_total = total_dimension(
        validated_dimensions
    )

    if not 0 <= index < dimension_total:
        raise ValueError(
            "Flat basis index lies outside the total "
            "Hilbert-space dimension."
        )

    occupations = np.unravel_index(
        index,
        validated_dimensions,
        order="C",
    )

    return tuple(
        int(occupation)
        for occupation in occupations
    )


def partial_trace(
    state: QuantumStateArray,
    dimensions: Sequence[int],
    *,
    trace_out: int | Sequence[int],
) -> ComplexMatrix:
    """
    Trace out selected modes from a multipartite state.

    Parameters
    ----------
    state:
        Composite ket or density matrix.

    dimensions:
        Hilbert-space dimension of every mode.

    trace_out:
        Mode index or sequence of mode indices to remove.

    Returns
    -------
    numpy.ndarray
        Reduced density matrix of the retained modes.

    Notes
    -----
    Mode numbering is zero-based.

    For example, with dimensions ``(d_A, d_B)``:

        trace_out=1

    returns

        rho_A = Tr_B(rho_AB).
    """
    validated_dimensions = validate_state_dimensions(
        state,
        dimensions,
    )

    number_modes = len(
        validated_dimensions
    )

    if isinstance(
        trace_out,
        (int, np.integer),
    ):
        traced_modes = (
            int(trace_out),
        )
    else:
        traced_modes = tuple(
            int(mode)
            for mode in trace_out
        )

    if len(traced_modes) == 0:
        return density_matrix(state)

    if len(set(traced_modes)) != len(
        traced_modes
    ):
        raise ValueError(
            "Each traced mode may be specified only once."
        )

    if any(
        mode < 0 or mode >= number_modes
        for mode in traced_modes
    ):
        raise ValueError(
            "A traced mode index is outside the valid range."
        )

    if len(traced_modes) == number_modes:
        raise ValueError(
            "Cannot trace out every mode. At least one mode "
            "must remain."
        )

    rho = density_matrix(state)

    tensor_shape = (
        *validated_dimensions,
        *validated_dimensions,
    )

    rho_tensor = rho.reshape(
        tensor_shape
    )

    remaining_dimensions = list(
        validated_dimensions
    )

    current_number_modes = number_modes

    for mode in sorted(
        traced_modes,
        reverse=True,
    ):
        rho_tensor = np.trace(
            rho_tensor,
            axis1=mode,
            axis2=(
                mode
                + current_number_modes
            ),
        )

        remaining_dimensions.pop(mode)

        current_number_modes -= 1

    reduced_dimension = int(
        np.prod(
            remaining_dimensions,
            dtype=np.int64,
        )
    )

    reduced_state = rho_tensor.reshape(
        reduced_dimension,
        reduced_dimension,
    )

    reduced_state = 0.5 * (
        reduced_state
        + reduced_state.conjugate().T
    )

    trace = np.trace(
        reduced_state
    )

    if np.isclose(
        abs(trace),
        0.0,
    ):
        raise ValueError(
            "Reduced state has zero trace."
        )

    reduced_state /= trace

    return np.asarray(
        reduced_state,
        dtype=np.complex128,
    )


def reduced_state(
    state: QuantumStateArray,
    dimensions: Sequence[int],
    *,
    keep: int | Sequence[int],
) -> ComplexMatrix:
    """
    Return the reduced state of selected modes.

    Parameters
    ----------
    state:
        Composite ket or density matrix.

    dimensions:
        Dimension of each mode.

    keep:
        Mode index or sequence of mode indices to retain.

    Returns
    -------
    numpy.ndarray
        Reduced density matrix of the retained subsystem.

    Notes
    -----
    The retained modes preserve their original ordering.

    For a state with modes ``(0, 1, 2)``, using

        keep=(2, 0)

    currently returns the retained modes in their original
    order ``(0, 2)``, not the requested order ``(2, 0)``.
    Mode permutation will be added separately.
    """
    validated_dimensions = validate_state_dimensions(
        state,
        dimensions,
    )

    number_modes = len(
        validated_dimensions
    )

    if isinstance(
        keep,
        (int, np.integer),
    ):
        kept_modes = (
            int(keep),
        )
    else:
        kept_modes = tuple(
            int(mode)
            for mode in keep
        )

    if len(kept_modes) == 0:
        raise ValueError(
            "At least one mode must be retained."
        )

    if len(set(kept_modes)) != len(
        kept_modes
    ):
        raise ValueError(
            "Each retained mode may be specified only once."
        )

    if any(
        mode < 0 or mode >= number_modes
        for mode in kept_modes
    ):
        raise ValueError(
            "A retained mode index is outside the valid range."
        )

    if len(kept_modes) == number_modes:
        return density_matrix(state)

    traced_modes = tuple(
        mode
        for mode in range(number_modes)
        if mode not in kept_modes
    )

    return partial_trace(
        state,
        validated_dimensions,
        trace_out=traced_modes,
    )


def product_state_dimensions(
    *states: QuantumStateArray,
) -> Dimensions:
    """
    Infer subsystem dimensions for a tensor product.

    Each supplied input is treated as one subsystem.
    """
    if len(states) == 0:
        raise ValueError(
            "At least one state is required."
        )

    dimensions: list[int] = []

    for state in states:
        state_array = np.asarray(
            state,
            dtype=np.complex128,
        )

        if state_array.ndim == 1:
            dimensions.append(
                int(state_array.size)
            )

        elif (
            state_array.ndim == 2
            and state_array.shape[0]
            == state_array.shape[1]
        ):
            dimensions.append(
                int(state_array.shape[0])
            )

        else:
            raise ValueError(
                "Each subsystem must be a ket or square "
                "density matrix."
            )

    return tuple(dimensions)

