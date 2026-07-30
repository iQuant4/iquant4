"""Fast sign-free tomography showcase with optional CVXPY execution."""

from __future__ import annotations

import importlib.util
from dataclasses import asdict, dataclass
from pathlib import Path

import numpy as np
from matplotlib.figure import Figure

from iqcore.measurements import (
    build_measurement_operators,
    histogram_probabilities,
    pure_state_quadrature_probability_density,
    sample_from_density,
    sign_free_samples,
)
from iqcore.metrics import pure_state_fidelity
from iqcore.states import fock_state
from iqcore.tomography import reconstruct_density_matrix, validate_measurement_matrix

from ._artifacts import prepare_output_directory, write_json


@dataclass(frozen=True, slots=True)
class TomographyShowcaseConfiguration:
    """Small, deterministic tomography configuration for the alpha showcase."""

    photon_number: int = 1
    cutoff: int = 12
    phases: int = 8
    bins: int = 32
    samples_per_phase: int = 2_000
    histogram_limit: float = 5.0
    grid_points: int = 4_001
    integration_points: int = 7
    photon_penalty: float = 1e-7
    seed: int = 7

    def __post_init__(self) -> None:
        if self.photon_number < 0 or self.photon_number >= self.cutoff:
            raise ValueError("photon_number must lie inside the Fock cutoff.")
        if self.cutoff <= 1:
            raise ValueError("cutoff must be greater than 1.")
        if self.phases < 2 or self.bins < 4:
            raise ValueError("Use at least two phases and four bins.")
        if self.samples_per_phase <= 0:
            raise ValueError("samples_per_phase must be positive.")
        if self.histogram_limit <= 0.0:
            raise ValueError("histogram_limit must be positive.")
        if self.grid_points < 101:
            raise ValueError("grid_points must be at least 101.")
        if self.integration_points < 2:
            raise ValueError("integration_points must be at least 2.")


@dataclass(frozen=True, slots=True)
class TomographyShowcaseResult:
    """Result and artifacts from the sign-free tomography showcase."""

    output_directory: Path
    status: str
    json_path: Path
    figure_path: Path | None
    fidelity: float | None
    probability_rmse: float | None
    vectorization_error: float | None


def cvxpy_available() -> bool:
    """Return whether the optional tomography solver dependency is installed."""
    return importlib.util.find_spec("cvxpy") is not None


def run_sign_free_tomography_showcase(
    output_directory: str | Path,
    configuration: TomographyShowcaseConfiguration | None = None,
    *,
    require_cvxpy: bool = False,
) -> TomographyShowcaseResult:
    """Reconstruct a Fock state from sign-free quadrature histograms."""
    config = configuration or TomographyShowcaseConfiguration()
    root = prepare_output_directory(output_directory) / "sign_free_tomography"
    root.mkdir(parents=True, exist_ok=True)
    json_path = root / "tomography_summary.json"

    if not cvxpy_available():
        if require_cvxpy:
            raise RuntimeError(
                "CVXPY is required for the tomography showcase. "
                "Install iq4comm[tomography]."
            )
        write_json(
            json_path,
            {
                "showcase": "sign-free-tomography",
                "status": "skipped",
                "reason": "CVXPY is not installed.",
                "configuration": asdict(config),
            },
        )
        return TomographyShowcaseResult(
            output_directory=root,
            status="skipped",
            json_path=json_path,
            figure_path=None,
            fidelity=None,
            probability_rmse=None,
            vectorization_error=None,
        )

    target_state = fock_state(config.photon_number, config.cutoff)
    target_density_matrix = np.outer(target_state, target_state.conjugate())
    phases = np.linspace(0.0, np.pi, config.phases, endpoint=False)
    bin_edges = np.linspace(0.0, config.histogram_limit, config.bins + 1)
    grid = np.linspace(
        -config.histogram_limit,
        config.histogram_limit,
        config.grid_points,
    )
    rng = np.random.default_rng(config.seed)
    samples_by_phase: list[np.ndarray] = []

    for phase in phases:
        density = pure_state_quadrature_probability_density(
            target_state,
            grid,
            float(phase),
        )
        ordinary_samples = sample_from_density(
            grid,
            density,
            config.samples_per_phase,
            rng,
        )
        samples_by_phase.append(sign_free_samples(ordinary_samples))

    measured_probabilities = histogram_probabilities(
        samples_by_phase,
        bin_edges,
    )
    operators = build_measurement_operators(
        phases,
        bin_edges,
        config.cutoff,
        config.integration_points,
    )
    vectorization_error = validate_measurement_matrix(
        operators,
        target_density_matrix,
        config.cutoff,
    )
    reconstruction = reconstruct_density_matrix(
        measured_probabilities,
        operators,
        config.cutoff,
        config.photon_penalty,
        "SCS",
    )
    fidelity = pure_state_fidelity(reconstruction.density_matrix, target_state)
    probability_rmse = float(
        np.sqrt(
            np.mean(
                (
                    reconstruction.predicted_probabilities
                    - reconstruction.measured_probabilities
                )
                ** 2
            )
        )
    )
    trace_value = float(np.real(np.trace(reconstruction.density_matrix)))
    minimum_eigenvalue = float(
        np.min(np.linalg.eigvalsh(reconstruction.density_matrix))
    )

    payload = {
        "showcase": "sign-free-tomography",
        "status": "completed",
        "configuration": asdict(config),
        "solver_status": reconstruction.solver_status,
        "objective_value": reconstruction.objective_value,
        "fidelity": fidelity,
        "probability_rmse": probability_rmse,
        "vectorization_error": vectorization_error,
        "trace": trace_value,
        "minimum_eigenvalue": minimum_eigenvalue,
    }
    write_json(json_path, payload)

    ideal_diagonal = np.abs(target_state) ** 2
    reconstructed_diagonal = np.real(np.diag(reconstruction.density_matrix))
    photon_numbers = np.arange(config.cutoff)
    figure = Figure(figsize=(9.0, 4.2))
    axes_distribution, axes_matrix = figure.subplots(1, 2)
    axes_distribution.bar(
        photon_numbers - 0.2,
        ideal_diagonal,
        width=0.4,
        label="Ideal",
    )
    axes_distribution.bar(
        photon_numbers + 0.2,
        reconstructed_diagonal,
        width=0.4,
        label="Reconstructed",
    )
    axes_distribution.set_xlabel("Photon number")
    axes_distribution.set_ylabel("Population")
    axes_distribution.set_title(f"Fock |{config.photon_number}> populations")
    axes_distribution.legend()

    image = axes_matrix.imshow(
        np.real(reconstruction.density_matrix),
        origin="lower",
        aspect="equal",
        interpolation="nearest",
        cmap="RdBu_r",
    )
    axes_matrix.set_xlabel("Fock index n")
    axes_matrix.set_ylabel("Fock index m")
    axes_matrix.set_title(f"Reconstructed density matrix\nF={fidelity:.4f}")
    figure.colorbar(image, ax=axes_matrix, fraction=0.046, pad=0.04)
    figure.tight_layout()
    figure_path = root / "tomography_reconstruction.png"
    figure.savefig(figure_path, dpi=180)

    return TomographyShowcaseResult(
        output_directory=root,
        status="completed",
        json_path=json_path,
        figure_path=figure_path,
        fidelity=fidelity,
        probability_rmse=probability_rmse,
        vectorization_error=vectorization_error,
    )


__all__ = [
    "TomographyShowcaseConfiguration",
    "TomographyShowcaseResult",
    "cvxpy_available",
    "run_sign_free_tomography_showcase",
]
