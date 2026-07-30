from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

from iq4comm.analysis.receiver_family import ReceiverFamilyConfiguration
from iq4comm.cli import main as cli_main
from iq4comm.showcase import (
    LossyCatConfiguration,
    ShowcaseDashboardResult,
    build_showcase_dashboard,
    open_showcase_dashboard,
    run_alpha_showcase,
    showcase_dashboard_payload,
)
import iq4comm.showcase.dashboard as dashboard_module


@pytest.fixture(scope="module")
def generated_dashboard(tmp_path_factory):
    root = tmp_path_factory.mktemp("iquant4_dashboard")
    manifest = run_alpha_showcase(
        root,
        include_tomography=False,
        receiver_configuration=ReceiverFamilyConfiguration(
            distances_km=(0.0, 20.0),
            max_pnr_threshold=10,
            homodyne_threshold_step=0.5,
            heterodyne_threshold_step=0.5,
        ),
        lossy_cat_configuration=LossyCatConfiguration(
            alpha=1.0,
            cutoff=14,
            transmissivities=(1.0, 0.5),
            extent=4.0,
            grid_points=61,
        ),
    )
    return root, manifest


def test_alpha_showcase_builds_dashboard_artifacts(generated_dashboard) -> None:
    root, _ = generated_dashboard
    for name in (
        "index.html",
        "iQuant4_showcase_standalone.html",
        "dashboard_data.json",
    ):
        path = root / name
        assert path.is_file()
        assert path.stat().st_size > 100


def test_dashboard_html_is_offline_and_branded(generated_dashboard) -> None:
    root, _ = generated_dashboard
    html = (root / "index.html").read_text(encoding="utf-8")
    assert "iQuant4 Developer Alpha Showcase" in html
    assert "Solutions" in html
    assert "Convenience" in html
    assert "Experience" in html
    assert "receiver_family/receiver_family_ber.png" in html
    assert "lossy_cat/lossy_cat_wigner.png" in html
    assert "https://" not in html
    assert "http://" not in html


def test_standalone_dashboard_embeds_figures(generated_dashboard) -> None:
    root, _ = generated_dashboard
    html = (root / "iQuant4_showcase_standalone.html").read_text(
        encoding="utf-8"
    )
    assert html.count("data:image/png;base64,") >= 2
    assert len(html) > (root / "index.html").stat().st_size


def test_dashboard_data_summarizes_scientific_outputs(generated_dashboard) -> None:
    root, _ = generated_dashboard
    payload = json.loads((root / "dashboard_data.json").read_text(encoding="utf-8"))
    assert payload["product"] == "iQuant4Comm"
    assert payload["active_packages"] == ["iqcore", "iq4comm"]
    assert payload["receiver_family"]["distance_count"] == 2
    assert sum(payload["receiver_family"]["winner_counts"].values()) == 2
    assert payload["lossy_cat"]["initial_transmissivity"] == 1.0
    assert payload["lossy_cat"]["final_transmissivity"] == 0.5
    assert payload["sign_free_tomography"]["status"] == "not-requested"


def test_dashboard_manifest_paths_are_portable(generated_dashboard) -> None:
    root, manifest = generated_dashboard
    payload = json.loads((root / "showcase_manifest.json").read_text(encoding="utf-8"))
    assert payload["dashboard"]["status"] == "completed"
    assert payload["dashboard"]["artifacts"] == [
        "index.html",
        "iQuant4_showcase_standalone.html",
        "dashboard_data.json",
    ]
    assert Path(manifest["dashboard_path"]).resolve() == (root / "index.html").resolve()
    assert all(not Path(path).is_absolute() for path in payload["dashboard"]["artifacts"])


def test_dashboard_public_api_is_available(generated_dashboard) -> None:
    root, _ = generated_dashboard
    result = build_showcase_dashboard(root)
    assert isinstance(result, ShowcaseDashboardResult)
    payload = showcase_dashboard_payload(root)
    assert payload["dashboard"] == "iQuant4 developer-alpha showcase"


def test_dashboard_cli_rebuilds_existing_output(
    generated_dashboard,
    tmp_path: Path,
    capsys,
) -> None:
    root, _ = generated_dashboard
    copied = tmp_path / "showcase"
    shutil.copytree(root, copied)
    for name in (
        "index.html",
        "iQuant4_showcase_standalone.html",
        "dashboard_data.json",
    ):
        (copied / name).unlink()

    exit_code = cli_main(
        ["showcase", "dashboard", "--output-dir", str(copied)]
    )
    assert exit_code == 0
    assert (copied / "index.html").is_file()
    assert "Standalone dashboard" in capsys.readouterr().out


def test_dashboard_cli_reports_missing_manifest(tmp_path: Path, capsys) -> None:
    exit_code = cli_main(
        ["showcase", "dashboard", "--output-dir", str(tmp_path)]
    )
    assert exit_code == 2
    assert "Run 'iq4comm showcase all' first" in capsys.readouterr().err


def test_dashboard_open_uses_default_browser(
    generated_dashboard,
    monkeypatch,
) -> None:
    root, _ = generated_dashboard
    opened: list[str] = []
    monkeypatch.setattr(
        dashboard_module.webbrowser,
        "open",
        lambda uri: opened.append(uri) or True,
    )
    assert open_showcase_dashboard(root / "index.html")
    assert opened and opened[0].startswith("file:")


def test_dashboard_generation_can_be_disabled(tmp_path: Path) -> None:
    manifest = run_alpha_showcase(
        tmp_path,
        include_tomography=False,
        include_dashboard=False,
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
    assert manifest["dashboard"]["status"] == "not-requested"
    assert not (tmp_path / "index.html").exists()
