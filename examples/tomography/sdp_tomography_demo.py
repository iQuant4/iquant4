from __future__ import annotations

import numpy as np
import matplotlib.pyplot as plt

from iqcore.measurements.homodyne_sampling import (
    quadrature_probability_density,
    sample_from_density,
)
from iqcore.states import fock_state
from iqcore.measurements import (
    build_measurement_operators,
    histogram_probabilities,
)
from iqcore.metrics import (
    pure_state_fidelity,
)
from iqcore.tomography import (
    reconstruct_density_matrix,
)


def main() -> None:
    # Parameters matching the simulated single-photon
    # example in the paper.
    cutoff = 20
    number_of_bins = 40
    histogram_limit = 5.0
    number_of_phases = 10
    samples_per_phase = 5_000

    seed = 7
    rng = np.random.default_rng(seed)

    target_state = fock_state(
        photon_number=1,
        cutoff=cutoff,
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
        5001,
    )

    samples_by_phase: list[np.ndarray] = []

    print("Generating sign-free quadrature data...")

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

    measured_probabilities = histogram_probabilities(
        samples_by_phase=samples_by_phase,
        bin_edges=bin_edges,
    )

    print()
    print("Constructing sign-free POVM operators...")

    measurement_operators = (
        build_measurement_operators(
            phases=phases,
            bin_edges=bin_edges,
            cutoff=cutoff,
            integration_points=9,
        )
    )

    print(
        f"Number of measurement operators: "
        f"{len(measurement_operators)}"
    )

    print()
    print("Solving semidefinite program...")

    result = reconstruct_density_matrix(
        measured_probabilities=(
            measured_probabilities
        ),
        measurement_operators=(
            measurement_operators
        ),
        cutoff=cutoff,
        photon_penalty=1e-7,
    )

    fidelity = pure_state_fidelity(
        density_matrix=result.density_matrix,
        target_state=target_state,
    )

    trace_value = np.real(
        np.trace(
            result.density_matrix
        )
    )

    eigenvalues = np.linalg.eigvalsh(
        result.density_matrix
    )

    diagonal = np.real(
        np.diag(
            result.density_matrix
        )
    )

    root_mean_square_error = np.sqrt(
        np.mean(
            (
                result.predicted_probabilities
                - result.measured_probabilities
            )
            ** 2
        )
    )

    print()
    print("iQuant4 Sign-Free SDP Tomography")
    print("--------------------------------")
    print("Target state          : |1>")
    print(f"Fock cutoff           : {cutoff}")
    print(
        f"Number of phases      : "
        f"{number_of_phases}"
    )
    print(
        f"Bins per phase        : "
        f"{number_of_bins}"
    )
    print(
        f"Samples per phase     : "
        f"{samples_per_phase}"
    )
    print(
        f"Total samples         : "
        f"{number_of_phases * samples_per_phase}"
    )
    print(
        f"Solver status         : "
        f"{result.solver_status}"
    )
    print(
        f"Objective value       : "
        f"{result.objective_value:.8e}"
    )
    print(
        f"Probability RMSE      : "
        f"{root_mean_square_error:.8e}"
    )
    print(
        f"Trace(rho)            : "
        f"{trace_value:.8f}"
    )
    print(
        f"Minimum eigenvalue    : "
        f"{np.min(eigenvalues):.8e}"
    )
    print(
        f"Reconstruction fidelity: "
        f"{fidelity:.8f}"
    )
    print()
    print("Largest diagonal elements:")

    sorted_indices = np.argsort(
        diagonal
    )[::-1]

    for index in sorted_indices[:5]:
        print(
            f"  rho[{index},{index}]"
            f" = {diagonal[index]:.8f}"
        )

    photon_numbers = np.arange(
        cutoff
    )

    plt.figure(
        figsize=(8, 5)
    )

    plt.bar(
        photon_numbers,
        diagonal,
        label="Reconstructed diagonal",
    )

    ideal_diagonal = np.zeros(
        cutoff
    )
    ideal_diagonal[1] = 1.0

    plt.plot(
        photon_numbers,
        ideal_diagonal,
        "o",
        label=r"Ideal $|1\rangle$",
    )

    plt.xlabel("Photon number")
    plt.ylabel(r"$\rho_{nn}$")
    plt.title(
        "Sign-Free SDP Reconstruction"
    )
    plt.xticks(
        photon_numbers
    )
    plt.legend()
    plt.tight_layout()
    plt.show()

    plt.figure(
        figsize=(8, 5)
    )

    plt.scatter(
        result.measured_probabilities,
        result.predicted_probabilities,
        s=18,
    )

    probability_maximum = max(
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
        [0.0, probability_maximum],
        [0.0, probability_maximum],
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
        "Measured vs Reconstructed Statistics"
    )
    plt.legend()
    plt.tight_layout()
    plt.show()


if __name__ == "__main__":
    main()