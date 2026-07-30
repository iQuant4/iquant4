from __future__ import annotations

import importlib.util

import numpy as np
import pytest

from iqcore.measurements import (
    build_measurement_operators,
    histogram_probabilities,
    integrate_sign_free_povm_bin,
    quadrature_bra_coefficients,
    sign_free_povm_density,
)
from iqcore.metrics import pure_state_fidelity
from iqcore.states import coherent_state, density_matrix, fock_state
from iqcore.tomography import (
    build_linear_measurement_matrix,
    reconstruct_density_matrix,
    validate_measurement_matrix,
)


def test_quadrature_bra_coefficients() -> None:
    coefficients = quadrature_bra_coefficients(
        x=0.0,
        phase=0.37,
        cutoff=6,
    )

    assert coefficients.shape == (6,)
    assert coefficients[0] == pytest.approx(np.pi ** (-0.25))
    assert coefficients[1] == pytest.approx(0.0)
    assert np.all(np.isfinite(coefficients))


def test_sign_free_povm_density_is_hermitian_and_positive() -> None:
    operator = sign_free_povm_density(
        x_absolute=0.8,
        phase=0.41,
        cutoff=8,
    )

    assert operator == pytest.approx(
        operator.conjugate().T,
        abs=1e-13,
    )
    assert np.min(np.linalg.eigvalsh(operator)) >= -1e-12


def test_integrated_sign_free_povm_bin() -> None:
    operator = integrate_sign_free_povm_bin(
        lower_edge=0.2,
        upper_edge=0.5,
        phase=0.3,
        cutoff=6,
        integration_points=7,
    )

    assert operator.shape == (6, 6)
    assert operator == pytest.approx(
        operator.conjugate().T,
        abs=1e-13,
    )
    assert np.trace(operator).real > 0.0


def test_build_measurement_operators_count_and_shape() -> None:
    phases = np.array([0.0, np.pi / 4.0, np.pi / 2.0])
    bin_edges = np.linspace(0.0, 3.0, 7)

    operators = build_measurement_operators(
        phases=phases,
        bin_edges=bin_edges,
        cutoff=5,
        integration_points=5,
    )

    assert len(operators) == 3 * 6
    assert all(operator.shape == (5, 5) for operator in operators)


def test_histogram_probabilities_normalize_each_phase() -> None:
    samples = [
        np.array([0.1, 0.2, 0.7, 1.1]),
        np.array([0.3, 0.4, 0.8, 1.4]),
    ]
    bin_edges = np.array([0.0, 0.5, 1.0, 1.5])

    probabilities = histogram_probabilities(
        samples_by_phase=samples,
        bin_edges=bin_edges,
    )

    assert probabilities.shape == (6,)
    assert np.sum(probabilities[:3]) == pytest.approx(1.0)
    assert np.sum(probabilities[3:]) == pytest.approx(1.0)


def test_linear_measurement_matrix_matches_direct_trace() -> None:
    phases = np.array([0.0, np.pi / 3.0])
    bin_edges = np.linspace(0.0, 4.0, 9)
    cutoff = 5
    operators = build_measurement_operators(
        phases=phases,
        bin_edges=bin_edges,
        cutoff=cutoff,
        integration_points=5,
    )
    state = coherent_state(alpha=0.6 + 0.2j, cutoff=cutoff)
    rho = density_matrix(state)

    matrix = build_linear_measurement_matrix(
        measurement_operators=operators,
        cutoff=cutoff,
    )

    assert matrix.shape == (len(operators), cutoff * cutoff)
    assert validate_measurement_matrix(
        measurement_operators=operators,
        density_matrix=rho,
        cutoff=cutoff,
    ) < 1e-12


def test_pure_state_fidelity() -> None:
    target = fock_state(photon_number=2, cutoff=6)
    orthogonal = fock_state(photon_number=1, cutoff=6)

    assert pure_state_fidelity(
        density_matrix(target),
        target,
    ) == pytest.approx(1.0)
    assert pure_state_fidelity(
        density_matrix(orthogonal),
        target,
    ) == pytest.approx(0.0)


@pytest.mark.skipif(
    importlib.util.find_spec("cvxpy") is None,
    reason="CVXPY is not installed in this test environment.",
)
def test_sdp_reconstruction_of_informationally_complete_qubit() -> None:
    cutoff = 2
    ket = np.array(
        [1.0, np.exp(0.3j)],
        dtype=np.complex128,
    ) / np.sqrt(2.0)
    rho = density_matrix(ket)

    zero = np.array([1.0, 0.0], dtype=np.complex128)
    one = np.array([0.0, 1.0], dtype=np.complex128)
    plus = np.array([1.0, 1.0], dtype=np.complex128) / np.sqrt(2.0)
    plus_i = np.array([1.0, 1.0j], dtype=np.complex128) / np.sqrt(2.0)
    operators = [
        np.outer(vector, vector.conjugate())
        for vector in (zero, one, plus, plus_i)
    ]
    probabilities = np.array(
        [np.trace(operator @ rho).real for operator in operators]
    )

    result = reconstruct_density_matrix(
        measured_probabilities=probabilities,
        measurement_operators=operators,
        cutoff=cutoff,
        photon_penalty=0.0,
        solver="SCS",
    )

    assert result.solver_status in {"optimal", "optimal_inaccurate"}
    assert np.trace(result.density_matrix).real == pytest.approx(
        1.0,
        abs=1e-6,
    )
    assert pure_state_fidelity(
        result.density_matrix,
        ket,
    ) > 0.999


@pytest.mark.parametrize(
    ("call", "message"),
    [
        (
            lambda: sign_free_povm_density(-0.1, 0.0, 4),
            "nonnegative",
        ),
        (
            lambda: integrate_sign_free_povm_bin(0.5, 0.5, 0.0, 4),
            "Upper edge",
        ),
        (
            lambda: build_measurement_operators(
                phases=np.array([]),
                bin_edges=np.array([0.0, 1.0]),
                cutoff=4,
            ),
            "At least one",
        ),
    ],
)
def test_sign_free_input_validation(call, message: str) -> None:
    with pytest.raises(ValueError, match=message):
        call()


def test_legacy_tomography_and_multimode_imports() -> None:
    from multimode import partial_trace as legacy_partial_trace
    from sign_free_tomography import (
        build_measurement_operators as legacy_build_measurement_operators,
        pure_state_fidelity as legacy_pure_state_fidelity,
        reconstruct_density_matrix as legacy_reconstruct_density_matrix,
    )

    from iqcore.states import partial_trace

    assert legacy_partial_trace is partial_trace
    assert legacy_build_measurement_operators is build_measurement_operators
    assert legacy_pure_state_fidelity is pure_state_fidelity
    assert legacy_reconstruct_density_matrix is reconstruct_density_matrix
