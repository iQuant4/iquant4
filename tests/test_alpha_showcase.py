from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from iq4comm.analysis.receiver_family import ReceiverFamilyConfiguration
from iq4comm.cli import main as cli_main
from iq4comm.showcase import (
    LossyCatConfiguration,
    TomographyShowcaseConfiguration,
    run_alpha_showcase,
    run_lossy_cat_showcase,
    run_receiver_family_showcase,
    run_sign_free_tomography_showcase,
)
import iq4comm.showcase.tomography as tomography_module


def assert_nonempty(path: Path) -> None:
    assert path.is_file()
    assert path.stat().st_size > 0


def test_receiver_family_showcase_writes_data_and_figure(tmp_path: Path) -> None:
    configuration = ReceiverFamilyConfiguration(
        distances_km=(0.0, 20.0),
        max_pnr_threshold=10,
        homodyne_threshold_step=0.5,
        heterodyne_threshold_step=0.5,
    )
    result = run_receiver_family_showcase(tmp_path, configuration)

    assert len(result.rows) == 2
    assert len(result.winners) == 2
    for path in (
        result.report_path,
        result.csv_path,
        result.json_path,
        result.figure_path,
    ):
        assert_nonempty(path)

    payload = json.loads(result.json_path.read_text(encoding="utf-8"))
    assert payload["showcase"] == "receiver-family"
    assert len(payload["rows"]) == 2
    assert payload["rows"][0]["winner"] in {
        "PNR",
        "Homodyne",
        "Heterodyne",
    }


def test_lossy_cat_showcase_tracks_loss_and_wigner_metrics(
    tmp_path: Path,
) -> None:
    configuration = LossyCatConfiguration(
        alpha=1.0,
        cutoff=14,
        transmissivities=(1.0, 0.5),
        extent=4.0,
        grid_points=61,
    )
    result = run_lossy_cat_showcase(tmp_path, configuration)

    assert len(result.rows) == 2
    for path in (result.csv_path, result.json_path, result.figure_path):
        assert_nonempty(path)

    initial, lossy = result.rows
    assert lossy.mean_photon_number == pytest_approx(
        0.5 * initial.mean_photon_number,
        rel=2e-6,
        abs=2e-8,
    )
    assert abs(initial.wigner_normalization - 1.0) < 3e-3
    assert abs(lossy.wigner_normalization - 1.0) < 3e-3
    assert lossy.wigner_negativity <= initial.wigner_negativity + 2e-3


def pytest_approx(value: float, **kwargs: float):
    import pytest

    return pytest.approx(value, **kwargs)


def test_tomography_showcase_records_optional_dependency_skip(
    tmp_path: Path,
    monkeypatch,
) -> None:
    monkeypatch.setattr(tomography_module, "cvxpy_available", lambda: False)
    result = run_sign_free_tomography_showcase(tmp_path)

    assert result.status == "skipped"
    assert result.figure_path is None
    assert result.fidelity is None
    assert_nonempty(result.json_path)
    payload = json.loads(result.json_path.read_text(encoding="utf-8"))
    assert payload["status"] == "skipped"
    assert "CVXPY" in payload["reason"]


def test_tomography_showcase_can_require_cvxpy(
    tmp_path: Path,
    monkeypatch,
) -> None:
    monkeypatch.setattr(tomography_module, "cvxpy_available", lambda: False)
    import pytest

    with pytest.raises(RuntimeError, match="CVXPY"):
        run_sign_free_tomography_showcase(tmp_path, require_cvxpy=True)


def test_alpha_showcase_writes_portable_manifest(tmp_path: Path) -> None:
    manifest = run_alpha_showcase(
        tmp_path,
        include_tomography=False,
        receiver_configuration=ReceiverFamilyConfiguration(
            distances_km=(0.0,),
            max_pnr_threshold=8,
            homodyne_threshold_step=0.75,
            heterodyne_threshold_step=0.75,
        ),
        lossy_cat_configuration=LossyCatConfiguration(
            alpha=1.0,
            cutoff=12,
            transmissivities=(1.0,),
            extent=3.5,
            grid_points=41,
        ),
    )

    manifest_path = Path(manifest["manifest_path"])
    assert_nonempty(manifest_path)
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert payload["receiver_family"]["status"] == "completed"
    assert payload["lossy_cat"]["status"] == "completed"
    assert payload["sign_free_tomography"]["status"] == "not-requested"
    for section in ("receiver_family", "lossy_cat"):
        for relative_path in payload[section]["artifacts"]:
            assert_nonempty(tmp_path / relative_path)


def test_showcase_cli_component_generates_artifacts(
    tmp_path: Path,
    capsys,
) -> None:
    exit_code = cli_main(
        [
            "showcase",
            "lossy-cat",
            "--output-dir",
            str(tmp_path),
        ]
    )
    assert exit_code == 0
    assert (tmp_path / "lossy_cat" / "lossy_cat_metrics.json").is_file()
    assert "showcase completed" in capsys.readouterr().out.lower()


def test_showcase_help_is_exposed_by_unified_cli(capsys) -> None:
    exit_code = cli_main(["--help"])
    assert exit_code == 0
    output = capsys.readouterr().out
    assert "showcase" in output


def test_showcase_configuration_validation() -> None:
    import pytest

    with pytest.raises(ValueError):
        LossyCatConfiguration(transmissivities=())
    with pytest.raises(ValueError):
        TomographyShowcaseConfiguration(photon_number=12, cutoff=12)
