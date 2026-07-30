from __future__ import annotations

import importlib
import runpy
from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:  # Python 3.10
    import tomli as tomllib


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def project_metadata() -> dict:
    return tomllib.loads(
        (PROJECT_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    )


def test_release_license_metadata_and_file_are_consistent() -> None:
    metadata = project_metadata()["project"]
    license_expression = metadata["license"]

    assert license_expression in {"Apache-2.0", "MIT"}
    assert metadata["license-files"] == ["LICENSE"]

    license_text = (PROJECT_ROOT / "LICENSE").read_text(encoding="utf-8")
    marker = (
        "Apache License"
        if license_expression == "Apache-2.0"
        else "Permission is hereby granted"
    )
    assert marker in license_text


def test_release_extra_declares_build_and_twine() -> None:
    release = project_metadata()["project"]["optional-dependencies"]["release"]
    assert any(value.startswith("build>=") for value in release)
    assert any(value.startswith("twine>=") for value in release)


def test_release_documents_and_community_files_exist() -> None:
    required = (
        "CONTRIBUTING.md",
        "SECURITY.md",
        "CITATION.cff",
        "ROADMAP.md",
        "CODE_OF_CONDUCT.md",
        "GOVERNANCE.md",
        "MANIFEST.in",
        "docs/release/checklist.md",
        "docs/release/public_api.md",
        "docs/release/publishing.md",
        "docs/release/validation.md",
        "docs/release/showcase.md",
        "docs/release/dashboard.md",
        "docs/release/documentation.md",
        "docs/release/public_preview.md",
        "docs/tutorials/showcase_dashboard.md",
        "docs/tutorials/alpha_showcase.md",
        "docs/development/legacy_compatibility.md",
        "docs/development/repository.md",
        "docs/release/github.md",
        ".github/dependabot.yml",
        ".github/PULL_REQUEST_TEMPLATE.md",
        ".github/workflows/pages.yml",
        ".github/workflows/release-candidate.yml",
        ".github/ISSUE_TEMPLATE/bug_report.yml",
        ".github/ISSUE_TEMPLATE/feature_request.yml",
    )
    assert all((PROJECT_ROOT / path).is_file() for path in required)


def test_readme_no_longer_contains_license_placeholder() -> None:
    readme = (PROJECT_ROOT / "README.md").read_text(encoding="utf-8")
    assert "A release license has not yet been selected" not in readme
    assert "License" in readme


def test_citation_matches_version_and_license() -> None:
    project = project_metadata()["project"]
    citation = (PROJECT_ROOT / "CITATION.cff").read_text(encoding="utf-8")
    assert f"version: {project['version']}" in citation
    assert f"license: {project['license']}" in citation
    assert "family-names: Yazdanpour" in citation
    assert "given-names: Amir" in citation


def test_public_api_documented_imports_resolve() -> None:
    expected = {
        "iqcore.states": ("coherent_state", "fock_state", "partial_trace"),
        "iqcore.measurements": ("quadrature_statistics",),
        "iqcore.optics": ("apply_beam_splitter",),
        "iqcore.phase_space": ("wigner_function",),
        "iq4comm": ("BinaryCoherentSource", "FiberChannel", "PNRReceiver"),
        "iq4comm.showcase": (
            "build_showcase_dashboard",
            "open_showcase_dashboard",
            "run_alpha_showcase",
            "run_lossy_cat_showcase",
            "run_receiver_family_showcase",
        ),
        "iq4comm.documentation": (
            "build_documentation_portal",
            "documentation_payload",
            "open_documentation_portal",
        ),
        "iq4comm.portal": (
            "build_public_preview",
            "open_public_preview",
        ),
    }
    for module_name, names in expected.items():
        module = importlib.import_module(module_name)
        assert all(hasattr(module, name) for name in names)


def test_release_tools_are_importable() -> None:
    for tool in (
        "generate_validation_report.py",
        "verify_release_gate.py",
        "verify_sdist.py",
        "verify_public_preview.py",
        "verify_repository_hygiene.py",
    ):
        namespace = runpy.run_path(
            str(PROJECT_ROOT / "tools" / tool),
            run_name=f"test_{tool}",
        )
        assert namespace


def test_validation_report_contains_reference_sections() -> None:
    report = (PROJECT_ROOT / "docs/release/validation.md").read_text(
        encoding="utf-8"
    )
    assert "Analytical and numerical checks" in report
    assert "HOM P(1,1)" in report
    assert "Receiver-family regression" in report
    assert "Scope and limitations" in report


def test_gitignore_excludes_local_migration_artifacts() -> None:
    gitignore = (PROJECT_ROOT / ".gitignore").read_text(encoding="utf-8")
    for pattern in ("/ALPHA_*/", "/CORE_*/", "archive/migrations/", ".venv/"):
        assert pattern in gitignore


def test_ci_builds_and_verifies_wheel_and_sdist() -> None:
    workflow = (PROJECT_ROOT / ".github/workflows/ci.yml").read_text(
        encoding="utf-8"
    )
    assert "python -m build --wheel --sdist" in workflow
    assert "python -m twine check" in workflow
    assert "verify_release_candidate.py" in workflow
