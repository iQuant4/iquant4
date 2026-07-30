from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray

from iqcore.states import ComplexMatrix

from .linear import build_linear_measurement_matrix


RealVector = NDArray[np.float64]


@dataclass(frozen=True)
class TomographyResult:
    density_matrix: ComplexMatrix
    predicted_probabilities: RealVector
    measured_probabilities: RealVector
    objective_value: float
    solver_status: str


def _load_cvxpy():
    """Import CVXPY only when SDP reconstruction is requested."""
    try:
        import cvxpy as cp
    except ImportError as exc:
        raise ImportError(
            "Semidefinite tomography requires CVXPY. "
            "Install the tomography dependencies before calling "
            "reconstruct_density_matrix()."
        ) from exc

    return cp


def reconstruct_density_matrix(
    measured_probabilities: RealVector,
    measurement_operators: list[ComplexMatrix],
    cutoff: int,
    photon_penalty: float = 1e-7,
    solver: str = "SCS",
) -> TomographyResult:
    """
    Reconstruct the density matrix using a vectorized SDP:

        minimize
            ||p_measured - A vec(rho)||_2^2
            + gamma Tr(rho N)

        subject to
            rho >= 0
            Tr(rho) = 1.
    """
    cp = _load_cvxpy()

    measured_probabilities = np.asarray(
        measured_probabilities,
        dtype=float,
    ).reshape(-1)

    if cutoff <= 0:
        raise ValueError(
            "Cutoff must be positive."
        )

    if photon_penalty < 0.0:
        raise ValueError(
            "Photon penalty cannot be negative."
        )

    if len(measurement_operators) != len(
        measured_probabilities
    ):
        raise ValueError(
            "The number of measurement operators must "
            "equal the number of measured probabilities."
        )

    measurement_matrix = (
        build_linear_measurement_matrix(
            measurement_operators=(
                measurement_operators
            ),
            cutoff=cutoff,
        )
    )

    rho = cp.Variable(
        (cutoff, cutoff),
        hermitian=True,
        name="rho",
    )

    rho_vector = cp.reshape(
        rho,
        (cutoff * cutoff,),
        order="C",
    )

    predicted_vector = cp.real(
        measurement_matrix
        @ rho_vector
    )

    number_operator = np.diag(
        np.arange(
            cutoff,
            dtype=float,
        )
    )

    data_mismatch = cp.sum_squares(
        predicted_vector
        - measured_probabilities
    )

    energy_regularization = (
        photon_penalty
        * cp.real(
            cp.trace(
                number_operator @ rho
            )
        )
    )

    objective = cp.Minimize(
        data_mismatch
        + energy_regularization
    )

    constraints = [
        rho >> 0,
        cp.real(
            cp.trace(rho)
        ) == 1.0,
    ]

    problem = cp.Problem(
        objective,
        constraints,
    )

    selected_solver = solver.upper()

    try:
        if selected_solver == "SCS":
            problem.solve(
                solver="SCS",
                eps=1e-6,
                max_iters=50_000,
                verbose=False,
            )
        else:
            problem.solve(
                solver=selected_solver,
                verbose=False,
            )

    except cp.error.SolverError:
        problem.solve(
            solver="SCS",
            eps=1e-6,
            max_iters=50_000,
            verbose=False,
        )

    if rho.value is None:
        raise RuntimeError(
            "The SDP solver did not return a density matrix."
        )

    reconstructed = np.asarray(
        rho.value,
        dtype=np.complex128,
    )

    # Suppress small solver-induced non-Hermitian errors.
    reconstructed = (
        reconstructed
        + reconstructed.conjugate().T
    ) / 2.0

    reconstructed_vector = reconstructed.reshape(
        cutoff * cutoff,
        order="C",
    )

    predicted_probabilities = np.real(
        measurement_matrix
        @ reconstructed_vector
    )

    objective_value = (
        float(problem.value)
        if problem.value is not None
        else float("nan")
    )

    return TomographyResult(
        density_matrix=reconstructed,
        predicted_probabilities=np.asarray(
            predicted_probabilities,
            dtype=float,
        ),
        measured_probabilities=(
            measured_probabilities
        ),
        objective_value=objective_value,
        solver_status=str(
            problem.status
        ),
    )


__all__ = [
    "RealVector",
    "TomographyResult",
    "reconstruct_density_matrix",
]
