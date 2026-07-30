from __future__ import annotations

import time

import matplotlib.pyplot as plt
import numpy as np

from iqcore.measurements.homodyne_sampling import (
    quadrature_probability_density,
    sample_from_density,
)
from iqcore.states import even_cat_state
from iqcore.measurements import (
    build_measurement_operators,
    histogram_probabilities,
)
from iqcore.metrics import (
    pure_state_fidelity,
)
from iqcore.tomography import (
    reconstruct_density_matrix,
    validate_measurement_matrix,
)


def main() -> None:
    # Reduced-scale validation parameters.
    alpha = 3.0

    cutoff = 35
    number_of_bins = 200
    histogram_limit = 8.0
    number_of_phases = 10
    samples_per_phase = 10_000

    integration_points = 9
    photon_penalty = 1e-7

    seed = 7
    rng = np.random.default_rng(seed)

    print("iQuant4 Sign-Free Cat-State Tomography")
    print("-------------------------------------")
    print(f"Cat amplitude          : {alpha}")
    print(f"Fock cutoff            : {cutoff}")
    print(f"Number of phases       : {number_of_phases}")
    print(f"Bins per phase         : {number_of_bins}")
    print(f"Samples per phase      : {samples_per_phase}")
    print(
        f"Total samples          : "
        f"{number_of_phases * samples_per_phase}"
    )
    print()

    target_state = even_cat_state(
        alpha=alpha,
        cutoff=cutoff,
    )

    target_density_matrix = np.outer(
        target_state,
        np.conjugate(target_state),
    )

    phases = np.linspace(
        0.0,
        np.pi,
        number_of_phases,
        endpoint=False,
    )

    bin_edges = np.linspace(
        0.0,
        histogram_limit,
        number_of_bins + 1,
    )

    x_grid = np.linspace(
        -histogram_limit,
        histogram_limit,
        7001,
    )

    samples_by_phase: list[np.ndarray] = []

    print("Generating sign-free quadrature samples...")

    sampling_start = time.perf_counter()

    for phase_index, phase in enumerate(phases):
        probability_density = (
            quadrature_probability_density(
                state=target_state,
                x_values=x_grid,
                phase=float(phase),
            )
        )

        ordinary_samples = sample_from_density(
            x_values=x_grid,
            probability_density=probability_density,
            sample_count=samples_per_phase,
            rng=rng,
        )

        sign_free_samples = np.abs(
            ordinary_samples
        )

        samples_by_phase.append(
            sign_free_samples
        )

        print(
            f"  Phase {phase_index + 1:>2}/"
            f"{number_of_phases}: "
            f"{phase:.4f} rad"
        )

    sampling_time = (
        time.perf_counter()
        - sampling_start
    )

    measured_probabilities = histogram_probabilities(
        samples_by_phase=samples_by_phase,
        bin_edges=bin_edges,
    )

    print()
    print(
        "Constructing integrated sign-free "
        "POVM operators..."
    )

    povm_start = time.perf_counter()

    measurement_operators = (
        build_measurement_operators(
            phases=phases,
            bin_edges=bin_edges,
            cutoff=cutoff,
            integration_points=integration_points,
        )
    )

    povm_time = (
        time.perf_counter()
        - povm_start
    )

    print(
        f"Number of operators    : "
        f"{len(measurement_operators)}"
    )

    matrix_validation_error = (
        validate_measurement_matrix(
            measurement_operators=measurement_operators,
            density_matrix=target_density_matrix,
            cutoff=cutoff,
        )
    )

    print(
        f"Vectorization check    : "
        f"{matrix_validation_error:.3e}"
    )

    print()
    print("Solving semidefinite program...")

    solver_start = time.perf_counter()

    result = reconstruct_density_matrix(
        measured_probabilities=measured_probabilities,
        measurement_operators=measurement_operators,
        cutoff=cutoff,
        photon_penalty=photon_penalty,
        solver="SCS",
    )

    solver_time = (
        time.perf_counter()
        - solver_start
    )

    reconstructed_density_matrix = (
        result.density_matrix
    )

    fidelity = pure_state_fidelity(
        density_matrix=reconstructed_density_matrix,
        target_state=target_state,
    )

    trace_value = float(
        np.real(
            np.trace(
                reconstructed_density_matrix
            )
        )
    )

    eigenvalues = np.linalg.eigvalsh(
        reconstructed_density_matrix
    )

    reconstructed_diagonal = np.real(
        np.diag(
            reconstructed_density_matrix
        )
    )

    ideal_diagonal = np.abs(
        target_state
    ) ** 2

    probability_rmse = float(
        np.sqrt(
            np.mean(
                (
                    result.predicted_probabilities
                    - result.measured_probabilities
                )
                ** 2
            )
        )
    )

    diagonal_rmse = float(
        np.sqrt(
            np.mean(
                (
                    reconstructed_diagonal
                    - ideal_diagonal
                )
                ** 2
            )
        )
    )

    odd_indices = np.arange(
        1,
        cutoff,
        2,
    )

    even_indices = np.arange(
        0,
        cutoff,
        2,
    )

    reconstructed_odd_population = float(
        np.sum(
            reconstructed_diagonal[
                odd_indices
            ]
        )
    )

    reconstructed_even_population = float(
        np.sum(
            reconstructed_diagonal[
                even_indices
            ]
        )
    )

    target_mean_photon_number = float(
        np.sum(
            np.arange(cutoff)
            * ideal_diagonal
        )
    )

    reconstructed_mean_photon_number = float(
        np.sum(
            np.arange(cutoff)
            * reconstructed_diagonal
        )
    )

    matrix_error = float(
        np.linalg.norm(
            reconstructed_density_matrix
            - target_density_matrix,
            ord="fro",
        )
    )

    print()
    print("Reconstruction results")
    print("----------------------")
    print(
        f"Solver status          : "
        f"{result.solver_status}"
    )
    print(
        f"Objective value        : "
        f"{result.objective_value:.8e}"
    )
    print(
        f"Probability RMSE       : "
        f"{probability_rmse:.8e}"
    )
    print(
        f"Diagonal RMSE          : "
        f"{diagonal_rmse:.8e}"
    )
    print(
        f"Trace(rho)             : "
        f"{trace_value:.8f}"
    )
    print(
        f"Minimum eigenvalue     : "
        f"{np.min(eigenvalues):.8e}"
    )
    print(
        f"Reconstruction fidelity: "
        f"{fidelity:.8f}"
    )
    print(
        f"Frobenius matrix error : "
        f"{matrix_error:.8e}"
    )
    print()
    print(
        f"Even population        : "
        f"{reconstructed_even_population:.8f}"
    )
    print(
        f"Odd population         : "
        f"{reconstructed_odd_population:.8e}"
    )
    print(
        f"Ideal mean photons     : "
        f"{target_mean_photon_number:.6f}"
    )
    print(
        f"Recovered mean photons : "
        f"{reconstructed_mean_photon_number:.6f}"
    )
    print()
    print("Execution times")
    print("---------------")
    print(
        f"Sampling               : "
        f"{sampling_time:.2f} s"
    )
    print(
        f"POVM construction      : "
        f"{povm_time:.2f} s"
    )
    print(
        f"SDP solver             : "
        f"{solver_time:.2f} s"
    )

    photon_numbers = np.arange(
        cutoff
    )

    plt.figure(
        figsize=(9, 5)
    )

    plt.bar(
        photon_numbers,
        reconstructed_diagonal,
        label="Reconstructed",
    )

    plt.plot(
        photon_numbers,
        ideal_diagonal,
        "o",
        label="Ideal even cat",
    )

    plt.xlabel("Photon number")
    plt.ylabel(r"$\rho_{nn}$")
    plt.title(
        rf"Even Cat-State Reconstruction, "
        rf"$\alpha={alpha}$"
    )
    plt.xticks(
        photon_numbers
    )
    plt.legend()
    plt.tight_layout()
    plt.show()

    plt.figure(
        figsize=(7, 6)
    )

    plt.imshow(
        np.real(
            target_density_matrix
        ),
        origin="lower",
        aspect="auto",
    )

    plt.colorbar(
        label=r"$\mathrm{Re}(\rho_{mn})$"
    )
    plt.xlabel("Photon number n")
    plt.ylabel("Photon number m")
    plt.title(
        "Ideal Cat-State Density Matrix"
    )
    plt.tight_layout()
    plt.show()

    plt.figure(
        figsize=(7, 6)
    )

    plt.imshow(
        np.real(
            reconstructed_density_matrix
        ),
        origin="lower",
        aspect="auto",
    )

    plt.colorbar(
        label=r"$\mathrm{Re}(\rho_{mn})$"
    )
    plt.xlabel("Photon number n")
    plt.ylabel("Photon number m")
    plt.title(
        "Reconstructed Cat-State Density Matrix"
    )
    plt.tight_layout()
    plt.show()

    plt.figure(
        figsize=(7, 6)
    )

    plt.imshow(
        np.abs(
            reconstructed_density_matrix
            - target_density_matrix
        ),
        origin="lower",
        aspect="auto",
    )

    plt.colorbar(
        label=(
            r"$|\rho_{\mathrm{rec}}"
            r"-\rho_{\mathrm{ideal}}|$"
        )
    )
    plt.xlabel("Photon number n")
    plt.ylabel("Photon number m")
    plt.title(
        "Absolute Density-Matrix Error"
    )
    plt.tight_layout()
    plt.show()

    plt.figure(
        figsize=(8, 5)
    )

    plt.scatter(
        result.measured_probabilities,
        result.predicted_probabilities,
        s=14,
    )

    maximum_probability = max(
        float(
            np.max(
                result.measured_probabilities
            )
        ),
        float(
            np.max(
                result.predicted_probabilities
            )
        ),
    )

    plt.plot(
        [0.0, maximum_probability],
        [0.0, maximum_probability],
        linestyle="--",
        label="Perfect agreement",
    )

    plt.xlabel(
        "Measured bin probability"
    )
    plt.ylabel(
        "Reconstructed bin probability"
    )
    plt.title(
        "Cat State: Measured vs Reconstructed"
    )
    plt.legend()
    plt.tight_layout()
    plt.show()


if __name__ == "__main__":
    main()