from __future__ import annotations

import json
import runpy
from pathlib import Path

import pytest

import iq4comm
from iq4comm.cli import main as cli_main
from iq4comm.diagnostics import (
    format_diagnostic_report,
    main as doctor_main,
    run_diagnostics,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_diagnostics_report_is_healthy_and_versioned() -> None:
    report = run_diagnostics()

    assert report.healthy
    assert report.iq4comm_version == iq4comm.__version__
    assert report.iqcore_version == iq4comm.__version__
    assert {check.name for check in report.checks} == {
        "version-sync",
        "vacuum-normalization",
        "vacuum-quadrature-variance",
        "fiber-transmissivity",
    }
    assert all(check.passed for check in report.checks)


def test_diagnostics_text_report_is_branded_and_complete() -> None:
    report = format_diagnostic_report(run_diagnostics())

    assert report.startswith("iQuant4Comm Doctor")
    assert "Status       : HEALTHY" in report
    assert "vacuum-quadrature-variance" in report
    assert "fiber-transmissivity" in report


def test_doctor_json_output_is_machine_readable(
    capsys: pytest.CaptureFixture[str],
) -> None:
    assert doctor_main(["--json"]) == 0

    payload = json.loads(capsys.readouterr().out)
    assert payload["healthy"] is True
    assert payload["iq4comm_version"] == iq4comm.__version__
    assert payload["checks"][0]["name"] == "version-sync"


def test_unified_cli_version_and_help(
    capsys: pytest.CaptureFixture[str],
) -> None:
    assert cli_main(["--version"]) == 0
    assert capsys.readouterr().out.strip() == iq4comm.__version__

    assert cli_main(["--help"]) == 0
    help_text = capsys.readouterr().out
    assert "iq4comm doctor" in help_text
    assert "iq4comm receiver-family" in help_text
    assert "iq4comm portal" in help_text


def test_unified_cli_delegates_receiver_family(
    capsys: pytest.CaptureFixture[str],
) -> None:
    assert (
        cli_main(
            [
                "receiver-family",
                "--distances",
                "0",
                "--threshold-step",
                "0.5",
                "--max-pnr-threshold",
                "8",
            ]
        )
        == 0
    )

    output = capsys.readouterr().out
    assert "iQuant4Comm Receiver-Family Comparison" in output
    assert "Winner" in output


def test_python_m_iq4comm_module_delegates_cli(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr("sys.argv", ["iq4comm", "--version"])

    with pytest.raises(SystemExit) as exit_info:
        runpy.run_module("iq4comm", run_name="__main__")

    assert exit_info.value.code == 0


def test_pyproject_declares_unified_and_legacy_console_scripts() -> None:
    pyproject = (PROJECT_ROOT / "pyproject.toml").read_text(encoding="utf-8")

    assert 'iq4comm = "iq4comm.cli:main"' in pyproject
    assert (
        'iq4comm-receiver-family = '
        '"iq4comm.analysis.receiver_family:main"'
    ) in pyproject
    assert "tomli>=2.0; python_version < '3.11'" in pyproject


def test_ci_workflow_covers_supported_platforms_and_clean_install() -> None:
    workflow = (
        PROJECT_ROOT / ".github" / "workflows" / "ci.yml"
    ).read_text(encoding="utf-8")

    assert "ubuntu-latest" in workflow
    assert "windows-latest" in workflow
    assert 'python: "3.10"' in workflow
    assert 'python: "3.14"' in workflow
    assert "python -m pytest -q" in workflow
    assert "verify_release_candidate.py" in workflow
    assert "verify_public_preview.py" in workflow


def test_release_candidate_tools_are_importable() -> None:
    namespace = runpy.run_path(
        str(PROJECT_ROOT / "tools" / "verify_clean_install.py"),
        run_name="verify_clean_install_module",
    )
    assert callable(namespace["verify_clean_install"])
    assert callable(namespace["metadata_version"])
