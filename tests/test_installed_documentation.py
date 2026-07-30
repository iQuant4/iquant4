from __future__ import annotations

import json
from pathlib import Path

import iqcore
import iq4comm
from iq4comm.cli import main as cli_main
from iq4comm.documentation import (
    DocumentationPortalResult,
    build_documentation_portal,
    documentation_payload,
    open_documentation_portal,
)
import iq4comm.documentation.portal as portal_module


def test_documentation_payload_tracks_active_packages_and_version() -> None:
    payload = documentation_payload()
    assert payload["version"] == iq4comm.__version__ == iqcore.__version__
    assert payload["active_packages"] == ["iqcore", "iq4comm"]
    assert payload["offline_ready"] is True
    assert payload["roadmap"][0] == {
        "branch": "iQuant4Comm",
        "status": "active",
    }


def test_documentation_portal_generates_required_artifacts(tmp_path: Path) -> None:
    result = build_documentation_portal(tmp_path / "documentation")
    assert isinstance(result, DocumentationPortalResult)
    for path in (
        result.index_path,
        result.iqcore_api_path,
        result.iq4comm_api_path,
        result.manifest_path,
        result.search_index_path,
        result.output_directory / "style.css",
        result.output_directory / "site.js",
        result.output_directory / "search_index.js",
    ):
        assert path.is_file()
        assert path.stat().st_size > 100
    assert result.page_count == 6
    assert result.symbol_count > 30


def test_documentation_portal_is_offline_and_branded(tmp_path: Path) -> None:
    result = build_documentation_portal(tmp_path / "documentation")
    index = result.index_path.read_text(encoding="utf-8")
    assert "Build with" in index
    assert "iQuant4Comm" in index
    assert "Solutions" in index
    assert "Convenience" in index
    assert "Experiences" in index
    assert "http://" not in index
    assert "https://" not in index


def test_generated_api_pages_contain_reference_symbols(tmp_path: Path) -> None:
    result = build_documentation_portal(tmp_path / "documentation")
    core = result.iqcore_api_path.read_text(encoding="utf-8")
    comm = result.iq4comm_api_path.read_text(encoding="utf-8")
    for marker in (
        "coherent_state",
        "apply_beam_splitter",
        "wigner_function",
        "reconstruct_density_matrix",
    ):
        assert marker in core
    for marker in (
        "BinaryCoherentSource",
        "FiberChannel",
        "ErasurePNRReceiver",
        "compare_receiver_families",
    ):
        assert marker in comm


def test_documentation_manifest_and_search_are_portable(tmp_path: Path) -> None:
    result = build_documentation_portal(tmp_path / "documentation")
    manifest = json.loads(result.manifest_path.read_text(encoding="utf-8"))
    search = json.loads(result.search_index_path.read_text(encoding="utf-8"))
    assert manifest["offline_ready"] is True
    assert manifest["active_packages"] == ["iqcore", "iq4comm"]
    assert all(not Path(page).is_absolute() for page in manifest["pages"])
    assert len(search) >= 10
    assert any(record["title"] == "iqcore.states" for record in search)
    assert any(record["title"] == "iq4comm.receivers" for record in search)


def test_documentation_cli_builds_portal(tmp_path: Path, capsys) -> None:
    output = tmp_path / "documentation"
    exit_code = cli_main(
        ["docs", "build", "--output-dir", str(output)]
    )
    assert exit_code == 0
    assert (output / "index.html").is_file()
    stdout = capsys.readouterr().out
    assert "iQuant4 documentation portal built" in stdout
    assert "API symbols" in stdout


def test_documentation_cli_requires_subcommand(capsys) -> None:
    exit_code = cli_main(["docs"])
    assert exit_code == 2
    assert "Build or open" in capsys.readouterr().err


def test_documentation_open_uses_default_browser(
    tmp_path: Path,
    monkeypatch,
) -> None:
    result = build_documentation_portal(tmp_path / "documentation")
    opened: list[str] = []
    monkeypatch.setattr(
        portal_module.webbrowser,
        "open",
        lambda uri: opened.append(uri) or True,
    )
    assert open_documentation_portal(result.output_directory)
    assert opened and opened[0].startswith("file:")


def test_documentation_public_api_is_intentional() -> None:
    import iq4comm.documentation as documentation

    assert documentation.__all__ == [
        "DocumentationPortalResult",
        "build_documentation_portal",
        "documentation_payload",
        "open_documentation_portal",
    ]
