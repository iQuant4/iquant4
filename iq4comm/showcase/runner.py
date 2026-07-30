"""Orchestrate the three flagship iQuant4 developer-alpha showcases."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from iq4comm.analysis.receiver_family import ReceiverFamilyConfiguration

from ._artifacts import (
    prepare_output_directory,
    relative_artifact_path,
    write_json,
)
from .dashboard import build_showcase_dashboard
from .lossy_cat import LossyCatConfiguration, run_lossy_cat_showcase
from .receiver_family import run_receiver_family_showcase
from .tomography import (
    TomographyShowcaseConfiguration,
    run_sign_free_tomography_showcase,
)


def run_alpha_showcase(
    output_directory: str | Path,
    *,
    include_tomography: bool = True,
    require_cvxpy: bool = False,
    include_dashboard: bool = True,
    receiver_configuration: ReceiverFamilyConfiguration | None = None,
    lossy_cat_configuration: LossyCatConfiguration | None = None,
    tomography_configuration: TomographyShowcaseConfiguration | None = None,
) -> dict[str, Any]:
    """Run the alpha showcase and return its manifest payload."""
    root = prepare_output_directory(output_directory)
    receiver = run_receiver_family_showcase(
        root, configuration=receiver_configuration
    )
    cat = run_lossy_cat_showcase(
        root, configuration=lossy_cat_configuration
    )

    tomography = None
    if include_tomography:
        tomography = run_sign_free_tomography_showcase(
            root,
            configuration=tomography_configuration,
            require_cvxpy=require_cvxpy,
        )

    manifest: dict[str, Any] = {
        "showcase": "iQuant4 developer alpha",
        "output_directory": str(root),
        "receiver_family": {
            "status": "completed",
            "winners": list(receiver.winners),
            "artifacts": [
                relative_artifact_path(receiver.report_path, root),
                relative_artifact_path(receiver.csv_path, root),
                relative_artifact_path(receiver.json_path, root),
                relative_artifact_path(receiver.figure_path, root),
            ],
        },
        "lossy_cat": {
            "status": "completed",
            "artifacts": [
                relative_artifact_path(cat.csv_path, root),
                relative_artifact_path(cat.json_path, root),
                relative_artifact_path(cat.figure_path, root),
            ],
        },
    }
    if tomography is not None:
        artifacts = [relative_artifact_path(tomography.json_path, root)]
        if tomography.figure_path is not None:
            artifacts.append(relative_artifact_path(tomography.figure_path, root))
        manifest["sign_free_tomography"] = {
            "status": tomography.status,
            "fidelity": tomography.fidelity,
            "artifacts": artifacts,
        }
    else:
        manifest["sign_free_tomography"] = {
            "status": "not-requested",
            "artifacts": [],
        }

    if include_dashboard:
        manifest["dashboard"] = {
            "status": "completed",
            "artifacts": [
                "index.html",
                "iQuant4_showcase_standalone.html",
                "dashboard_data.json",
            ],
        }
        dashboard = build_showcase_dashboard(root, manifest=manifest)
    else:
        manifest["dashboard"] = {
            "status": "not-requested",
            "artifacts": [],
        }
        dashboard = None

    manifest_path = write_json(root / "showcase_manifest.json", manifest)
    manifest["manifest_path"] = str(manifest_path)
    if dashboard is not None:
        manifest["dashboard_path"] = str(dashboard.html_path)
        manifest["standalone_dashboard_path"] = str(
            dashboard.standalone_html_path
        )
    return manifest


__all__ = ["run_alpha_showcase"]
