from __future__ import annotations

import json
from pathlib import Path

from iq4comm.cli import main as cli_main
from iq4comm.portal import (
    PublicPreviewResult,
    build_public_preview,
    open_public_preview,
)
import iq4comm.portal.site as site_module


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_docs_only_public_preview_generates_static_site(tmp_path: Path) -> None:
    result = build_public_preview(
        tmp_path / "public_preview",
        include_showcase=False,
    )
    assert isinstance(result, PublicPreviewResult)
    for path in (
        result.index_path,
        result.manifest_path,
        result.output_directory / "roadmap.html",
        result.output_directory / "404.html",
        result.output_directory / "portal.css",
        result.output_directory / "portal.js",
        result.output_directory / "docs" / "index.html",
        result.output_directory / ".nojekyll",
    ):
        assert path.is_file()
    assert result.showcase_generated is False
    assert result.showcase_directory is None


def test_public_preview_with_showcase_links_flagship_outputs(
    tmp_path: Path,
) -> None:
    result = build_public_preview(
        tmp_path / "public_preview",
        include_showcase=True,
        include_tomography=False,
    )
    assert result.showcase_generated is True
    assert result.showcase_directory is not None
    assert (result.showcase_directory / "index.html").is_file()
    assert (
        result.showcase_directory
        / "receiver_family"
        / "receiver_family_results.json"
    ).is_file()
    html = result.index_path.read_text(encoding="utf-8")
    assert "Receiver-family optimization" in html
    assert 'href="showcase/index.html"' in html


def test_public_preview_is_offline_branded_and_limitation_aware(
    tmp_path: Path,
) -> None:
    result = build_public_preview(
        tmp_path / "public_preview",
        include_showcase=False,
    )
    html = result.index_path.read_text(encoding="utf-8")
    assert "iQuant4" in html
    assert "iqcore" in html
    assert "iQuant4Comm" in html
    assert "Solutions" in html
    assert "Convenience" in html
    assert "Experiences" in html
    assert "Developer-alpha scope" in html
    assert "http://" not in html
    assert "https://" not in html


def test_public_preview_manifest_is_portable(tmp_path: Path) -> None:
    result = build_public_preview(
        tmp_path / "public_preview",
        include_showcase=False,
    )
    manifest = json.loads(result.manifest_path.read_text(encoding="utf-8"))
    assert manifest["offline_ready"] is True
    assert manifest["static_hosting_ready"] is True
    assert manifest["active_packages"] == ["iqcore", "iq4comm"]
    assert manifest["showcase"]["generated"] is False
    assert all(not Path(page).is_absolute() for page in manifest["pages"])


def test_public_preview_cli_builds_docs_only_site(
    tmp_path: Path,
    capsys,
) -> None:
    output = tmp_path / "public_preview"
    assert (
        cli_main(
            [
                "portal",
                "build",
                "--output-dir",
                str(output),
                "--skip-showcase",
            ]
        )
        == 0
    )
    assert (output / "index.html").is_file()
    assert (output / "docs" / "index.html").is_file()
    stdout = capsys.readouterr().out
    assert "iQuant4 public preview built" in stdout
    assert "Showcase   : False" in stdout


def test_public_preview_cli_requires_subcommand(capsys) -> None:
    assert cli_main(["portal"]) == 2
    assert "static iQuant4 public-preview portal" in capsys.readouterr().err


def test_open_public_preview_uses_default_browser(
    tmp_path: Path,
    monkeypatch,
) -> None:
    result = build_public_preview(
        tmp_path / "public_preview",
        include_showcase=False,
    )
    opened: list[str] = []
    monkeypatch.setattr(
        site_module.webbrowser,
        "open",
        lambda uri: opened.append(uri) or True,
    )
    assert open_public_preview(result.output_directory)
    assert opened and opened[0].startswith("file:")


def test_public_preview_public_api_is_intentional() -> None:
    import iq4comm.portal as portal

    assert portal.__all__ == [
        "PublicPreviewResult",
        "build_public_preview",
        "open_public_preview",
    ]


def test_public_preview_release_files_and_pages_workflow_exist() -> None:
    for path in (
        "ROADMAP.md",
        "CODE_OF_CONDUCT.md",
        "docs/release/public_preview.md",
        ".github/workflows/pages.yml",
    ):
        assert (PROJECT_ROOT / path).is_file()

    workflow = (PROJECT_ROOT / ".github/workflows/pages.yml").read_text(
        encoding="utf-8"
    )
    assert "workflow_dispatch" in workflow
    assert "actions/configure-pages@v5" in workflow
    assert "actions/upload-pages-artifact@v3" in workflow
    assert "actions/deploy-pages@v4" in workflow
    assert "python -m iq4comm portal build" in workflow
