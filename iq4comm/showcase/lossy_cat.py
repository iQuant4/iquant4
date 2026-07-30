"""Loss-degraded cat-state showcase for the shared iqcore engine."""

from __future__ import annotations

import csv
from dataclasses import asdict, dataclass
from pathlib import Path

import numpy as np
from matplotlib.figure import Figure

from iqcore.channels import pure_loss_channel
from iqcore.metrics import mean_photon_number, state_purity
from iqcore.phase_space import (
    wigner_function,
    wigner_negativity,
    wigner_normalization,
)
from iqcore.states import even_cat_state

from ._artifacts import prepare_output_directory, write_json


@dataclass(frozen=True, slots=True)
class LossyCatConfiguration:
    """Configuration for the loss-degraded cat-state showcase."""

    alpha: float = 1.5
    cutoff: int = 30
    transmissivities: tuple[float, ...] = (1.0, 0.8, 0.5, 0.2)
    extent: float = 5.0
    grid_points: int = 151

    def __post_init__(self) -> None:
        values = tuple(float(value) for value in self.transmissivities)
        object.__setattr__(self, "transmissivities", values)
        if self.alpha <= 0.0:
            raise ValueError("alpha must be positive.")
        if self.cutoff <= 1:
            raise ValueError("cutoff must be greater than 1.")
        if not values:
            raise ValueError("At least one transmissivity is required.")
        if any(not 0.0 <= value <= 1.0 for value in values):
            raise ValueError("Transmissivities must lie between 0 and 1.")
        if self.extent <= 0.0:
            raise ValueError("extent must be positive.")
        if self.grid_points < 21:
            raise ValueError("grid_points must be at least 21.")


@dataclass(frozen=True, slots=True)
class LossyCatRow:
    """State and phase-space metrics at one transmissivity."""

    transmissivity: float
    mean_photon_number: float
    purity: float
    wigner_normalization: float
    wigner_negativity: float


@dataclass(frozen=True, slots=True)
class LossyCatShowcaseResult:
    """Artifacts and metrics produced by the lossy-cat showcase."""

    output_directory: Path
    rows: tuple[LossyCatRow, ...]
    csv_path: Path
    json_path: Path
    figure_path: Path


def _write_rows(path: Path, rows: tuple[LossyCatRow, ...]) -> None:
    fieldnames = [
        "transmissivity",
        "mean_photon_number",
        "purity",
        "wigner_normalization",
        "wigner_negativity",
    ]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(asdict(row))


def run_lossy_cat_showcase(
    output_directory: str | Path,
    configuration: LossyCatConfiguration | None = None,
) -> LossyCatShowcaseResult:
    """Apply pure loss to an even cat state and save phase-space artifacts."""
    config = configuration or LossyCatConfiguration()
    root = prepare_output_directory(output_directory) / "lossy_cat"
    root.mkdir(parents=True, exist_ok=True)

    state = even_cat_state(alpha=config.alpha, cutoff=config.cutoff)
    grid = np.linspace(
        -config.extent,
        config.extent,
        config.grid_points,
        dtype=float,
    )

    rows: list[LossyCatRow] = []
    wigner_functions: list[np.ndarray] = []
    for transmissivity in config.transmissivities:
        output_state = pure_loss_channel(state, transmissivity=transmissivity)
        wigner = wigner_function(output_state, grid, grid)
        wigner_functions.append(wigner)
        rows.append(
            LossyCatRow(
                transmissivity=transmissivity,
                mean_photon_number=mean_photon_number(output_state),
                purity=state_purity(output_state),
                wigner_normalization=wigner_normalization(wigner, grid, grid),
                wigner_negativity=wigner_negativity(wigner, grid, grid),
            )
        )

    row_tuple = tuple(rows)
    csv_path = root / "lossy_cat_metrics.csv"
    _write_rows(csv_path, row_tuple)
    json_path = write_json(
        root / "lossy_cat_metrics.json",
        {
            "showcase": "lossy-cat",
            "configuration": asdict(config),
            "rows": [asdict(row) for row in row_tuple],
        },
    )

    columns = min(2, len(wigner_functions))
    rows_count = int(np.ceil(len(wigner_functions) / columns))
    figure = Figure(figsize=(5.0 * columns, 4.2 * rows_count))
    axes_array = np.atleast_1d(
        figure.subplots(rows_count, columns, squeeze=False)
    ).reshape(-1)
    maximum = max(float(np.max(np.abs(wigner))) for wigner in wigner_functions)

    for axes, transmissivity, wigner in zip(
        axes_array,
        config.transmissivities,
        wigner_functions,
        strict=False,
    ):
        image = axes.imshow(
            wigner,
            origin="lower",
            extent=[grid[0], grid[-1], grid[0], grid[-1]],
            aspect="equal",
            interpolation="bilinear",
            cmap="RdBu_r",
            vmin=-maximum,
            vmax=maximum,
        )
        axes.set_title(rf"$\eta={transmissivity:.2f}$")
        axes.set_xlabel(r"$x$")
        axes.set_ylabel(r"$p$")
        figure.colorbar(image, ax=axes, fraction=0.046, pad=0.04)

    for axes in axes_array[len(wigner_functions) :]:
        axes.set_visible(False)

    figure.suptitle("Loss-degraded even-cat Wigner functions")
    figure.tight_layout()
    figure_path = root / "lossy_cat_wigner.png"
    figure.savefig(figure_path, dpi=180)

    return LossyCatShowcaseResult(
        output_directory=root,
        rows=row_tuple,
        csv_path=csv_path,
        json_path=json_path,
        figure_path=figure_path,
    )


__all__ = [
    "LossyCatConfiguration",
    "LossyCatRow",
    "LossyCatShowcaseResult",
    "run_lossy_cat_showcase",
]
