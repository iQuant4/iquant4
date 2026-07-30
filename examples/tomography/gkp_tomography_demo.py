from __future__ import annotations

import time

import matplotlib.pyplot as plt
import numpy as np

from iqcore.measurements.homodyne_sampling import (
    quadrature_probability_density,
    sample_from_density,
)
from iqcore.states import approximate_gkp_state
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
    # Change this to True after the reduced test succeeds.
    paper_scale = True

    delta = 0.3
    kappa = 0.3

    logical_index = 0
    logical_dimension = 2
    lattice_cutoff = 6

    cutoff = 35
    histogram_limit = 8.0
    integration_points = 9
    photon_penalty = 1e-7

    if paper_scale:
        number_of_bins = 200
        number_of_phases = 40
        samples_per_phase = 20_000
    else:
        number_of_bins = 100
        number_of_phases = 20
        samples_per_phase = 10_000

    seed = 7
    rng = np.random.default_rng(seed)

    print("iQuant4 Sign-Free GKP-State Tomography")
    print("-------------------------------------")
    print(f"Delta                  : {delta}")
    print(f"Kappa                  : {kappa}")
    print(f"Logical index j        : {logical_index}")
    print(f"Logical dimension d    : {logical_dimension}")
    print(f"Lattice cutoff         : {lattice_cutoff}")
    print(f"Fock cutoff            : {cutoff}")
    print(f"Number of phases       : {number_of_phases}")
    print(f"Bins per phase         : {number_of_bins}")
    print(f"Samples per phase      : {samples_per_phase}")
    print(
        f"Total samples          : "
        f"{number_of_phases * samples_per_phase}"
    )
    print(
        f"Paper-scale mode       : "
        f"{paper_scale}"
    )
    print()

    print("Constructing approximate GKP state...")

    state_start = time.perf_counter()

    target_state = approximate_gkp_state(
        delta=delta,
        kappa=kappa,
        cutoff=cutoff,
        logical_index=logical_index,
        dimension=logical_dimension,
        lattice_cutoff=lattice_cutoff,
    )

    state_time = (
        time.perf_counter()
        - state_start
    )

    target_density_matrix = np.outer(
        target_state,
        np.conjugate(target_state),
    )

    ideal_diagonal = (
        np.abs(target_state) ** 2
    )

    ideal_even_population = float(
        np.sum(
            ideal_diagonal[0::2]
        )
    )

    ideal_odd_population = float(
        np.sum(
            ideal_diagonal[1::2]
        )
    )

    ideal_mean_photon_number = float(
        np.sum(
            np.arange(cutoff)
            * ideal_diagonal
        )
    )

    print(
        f"Ideal even population  : "
        f"{ideal_even_population:.8f}"
    )
    print(
        f"Ideal odd population   : "
        f"{ideal_odd_population:.8e}"
    )
    print(
        f"Ideal mean photons     : "
        f"{ideal_mean_photon_number:.6f}"
    )
    print()

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
        8001,
    )

    samples_by_phase: list[np.ndarray] = []

    print("Generating sign-free quadrature samples...")

    sampling_start = time.perf_counter()

    for phase_index, phase in enumerate(phases):
        density = quadrature_probability_density(
            state=target_state,
            x_values=x_grid,
            phase=float(phase),
        )

        ordinary_samples = sample_from_density(
            x_values=x_grid,
            probability_density=density,
            sample_count=samples_per_phase,
            rng=rng,
        )

        samples_by_phase.append(
            np.abs(ordinary_samples)
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

    validation_error = (
        validate_measurement_matrix(
            measurement_operators=measurement_operators,
            density_matrix=target_density_matrix,
            cutoff=cutoff,
        )
    )

    print(
        f"Vectorization check    : "
        f"{validation_error:.3e}"
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

    reconstructed_diagonal = np.real(
        np.diag(
            reconstructed_density_matrix
        )
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

    reconstructed_even_population = float(
        np.sum(
            reconstructed_diagonal[0::2]
        )
    )

    reconstructed_odd_population = float(
        np.sum(
            reconstructed_diagonal[1::2]
        )
    )

    reconstructed_mean_photon_number = float(
        np.sum(
            np.arange(cutoff)
            * reconstructed_diagonal
        )
    )

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
        f"Recovered even pop.    : "
        f"{reconstructed_even_population:.8f}"
    )
    print(
        f"Recovered odd pop.     : "
        f"{reconstructed_odd_population:.8e}"
    )
    print(
        f"Ideal mean photons     : "
        f"{ideal_mean_photon_number:.6f}"
    )
    print(
        f"Recovered mean photons : "
        f"{reconstructed_mean_photon_number:.6f}"
    )
    print()
    print("Execution times")
    print("---------------")
    print(
        f"State construction     : "
        f"{state_time:.2f} s"
    )
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
        figsize=(10, 5)
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
        label="Ideal approximate GKP",
    )

    plt.xlabel("Photon number")
    plt.ylabel(r"$\rho_{nn}$")
    plt.title(
        rf"GKP Reconstruction, "
        rf"$\Delta=\kappa={delta}$"
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
        "Ideal GKP Density Matrix"
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
        "Reconstructed GKP Density Matrix"
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
        "Absolute GKP Density-Matrix Error"
    )
    plt.tight_layout()
    plt.show()

    plt.figure(
        figsize=(8, 5)
    )

    plt.scatter(
        result.measured_probabilities,
        result.predicted_probabilities,
        s=12,
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
        "GKP: Measured vs Reconstructed"
    )
    plt.legend()
    plt.tight_layout()
    plt.show()


if __name__ == "__main__":
    main()