"""Receiver-family showcase with machine-readable and visual artifacts."""

from __future__ import annotations

import csv
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from matplotlib.figure import Figure

from iq4comm.analysis.receiver_family import (
    ReceiverFamilyConfiguration,
    ReceiverFamilyRow,
    compare_receiver_families,
    format_receiver_family_report,
    threshold_text,
)

from ._artifacts import prepare_output_directory, write_json


@dataclass(frozen=True, slots=True)
class ReceiverFamilyShowcaseResult:
    """Artifacts and optimized rows produced by the receiver showcase."""

    output_directory: Path
    rows: tuple[ReceiverFamilyRow, ...]
    report_path: Path
    csv_path: Path
    json_path: Path
    figure_path: Path

    @property
    def winners(self) -> tuple[str, ...]:
        """Return the winning receiver family at every distance."""
        return tuple(row.winner for row in self.rows)


def _receiver_payload(row: ReceiverFamilyRow, family: str) -> dict[str, Any]:
    result = row.results[family]
    metrics = result.metrics
    return {
        "thresholds": threshold_text(result.receiver),
        "acceptance_probability": metrics.acceptance_probability,
        "erasure_probability": metrics.erasure_probability,
        "unconditional_error_probability": (
            metrics.unconditional_error_probability
        ),
        "conditional_ber": metrics.conditional_ber,
    }


def receiver_family_payload(
    rows: tuple[ReceiverFamilyRow, ...],
    configuration: ReceiverFamilyConfiguration,
) -> dict[str, Any]:
    """Return a JSON-serializable receiver-family result."""
    return {
        "showcase": "receiver-family",
        "configuration": asdict(configuration),
        "rows": [
            {
                "distance_km": row.distance_km,
                "transmittance": row.transmittance,
                "received_mu_0": row.received_mu_0,
                "received_mu_1": row.received_mu_1,
                "winner": row.winner,
                "receivers": {
                    family: _receiver_payload(row, family)
                    for family in ("PNR", "Homodyne", "Heterodyne")
                },
            }
            for row in rows
        ],
    }


def _write_receiver_csv(path: Path, rows: tuple[ReceiverFamilyRow, ...]) -> None:
    fieldnames = [
        "distance_km",
        "transmittance",
        "received_mu_0",
        "received_mu_1",
        "pnr_thresholds",
        "pnr_acceptance",
        "pnr_conditional_ber",
        "homodyne_thresholds",
        "homodyne_acceptance",
        "homodyne_conditional_ber",
        "heterodyne_thresholds",
        "heterodyne_acceptance",
        "heterodyne_conditional_ber",
        "winner",
    ]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(
                {
                    "distance_km": row.distance_km,
                    "transmittance": row.transmittance,
                    "received_mu_0": row.received_mu_0,
                    "received_mu_1": row.received_mu_1,
                    "pnr_thresholds": threshold_text(row.pnr.receiver),
                    "pnr_acceptance": row.pnr.metrics.acceptance_probability,
                    "pnr_conditional_ber": row.pnr.metrics.conditional_ber,
                    "homodyne_thresholds": threshold_text(
                        row.homodyne.receiver
                    ),
                    "homodyne_acceptance": (
                        row.homodyne.metrics.acceptance_probability
                    ),
                    "homodyne_conditional_ber": (
                        row.homodyne.metrics.conditional_ber
                    ),
                    "heterodyne_thresholds": threshold_text(
                        row.heterodyne.receiver
                    ),
                    "heterodyne_acceptance": (
                        row.heterodyne.metrics.acceptance_probability
                    ),
                    "heterodyne_conditional_ber": (
                        row.heterodyne.metrics.conditional_ber
                    ),
                    "winner": row.winner,
                }
            )


def _plot_receiver_family(path: Path, rows: tuple[ReceiverFamilyRow, ...]) -> None:
    figure = Figure(figsize=(8.4, 5.2))
    axes = figure.subplots()
    distances = [row.distance_km for row in rows]

    for family, label in (
        ("PNR", "PNR"),
        ("Homodyne", "Homodyne"),
        ("Heterodyne", "Heterodyne"),
    ):
        values = [row.results[family].metrics.conditional_ber for row in rows]
        axes.semilogy(distances, values, marker="o", label=label)

    axes.set_xlabel("Fiber distance (km)")
    axes.set_ylabel("Conditional BER")
    axes.set_title("Optimized receiver-family comparison")
    axes.grid(True, which="both", alpha=0.25)
    axes.legend()
    figure.tight_layout()
    figure.savefig(path, dpi=180)


def run_receiver_family_showcase(
    output_directory: str | Path,
    configuration: ReceiverFamilyConfiguration | None = None,
) -> ReceiverFamilyShowcaseResult:
    """Run the receiver-family showcase and save all artifacts."""
    config = configuration or ReceiverFamilyConfiguration(
        distances_km=(0.0, 20.0, 40.0, 60.0),
        max_pnr_threshold=16,
        homodyne_threshold_step=0.1,
        heterodyne_threshold_step=0.1,
    )
    root = prepare_output_directory(output_directory) / "receiver_family"
    root.mkdir(parents=True, exist_ok=True)
    rows = compare_receiver_families(config)

    report_path = root / "receiver_family_report.txt"
    report_path.write_text(
        format_receiver_family_report(rows, config) + "\n",
        encoding="utf-8",
    )
    csv_path = root / "receiver_family_results.csv"
    _write_receiver_csv(csv_path, rows)
    json_path = write_json(
        root / "receiver_family_results.json",
        receiver_family_payload(rows, config),
    )
    figure_path = root / "receiver_family_ber.png"
    _plot_receiver_family(figure_path, rows)

    return ReceiverFamilyShowcaseResult(
        output_directory=root,
        rows=rows,
        report_path=report_path,
        csv_path=csv_path,
        json_path=json_path,
        figure_path=figure_path,
    )


__all__ = [
    "ReceiverFamilyShowcaseResult",
    "receiver_family_payload",
    "run_receiver_family_showcase",
]
