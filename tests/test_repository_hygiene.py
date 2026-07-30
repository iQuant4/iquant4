from __future__ import annotations

import runpy
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
NAMESPACE = runpy.run_path(
    str(PROJECT_ROOT / "tools" / "verify_repository_hygiene.py"),
    run_name="repository_hygiene_test",
)

REQUIRED_GITIGNORE_PATTERNS = NAMESPACE["REQUIRED_GITIGNORE_PATTERNS"]
DEFAULT_MAX_TRACKED_BYTES = NAMESPACE["DEFAULT_MAX_TRACKED_BYTES"]
is_forbidden_tracked_path = NAMESPACE["is_forbidden_tracked_path"]
verify_repository = NAMESPACE["verify_repository"]
_file_errors = NAMESPACE["_file_errors"]


def test_repository_policy_files_exist() -> None:
    required = (
        ".github/dependabot.yml",
        ".github/workflows/release-candidate.yml",
        "GOVERNANCE.md",
        "docs/development/repository.md",
        "docs/release/github.md",
        "tools/verify_repository_hygiene.py",
    )
    assert all((PROJECT_ROOT / path).is_file() for path in required)


def test_gitignore_contains_repository_safety_patterns() -> None:
    text = (PROJECT_ROOT / ".gitignore").read_text(encoding="utf-8")
    assert all(pattern in text for pattern in REQUIRED_GITIGNORE_PATTERNS)
    for pattern in ("credentials*.json", "secrets*.json", "token*.json"):
        assert pattern in text


def test_gitattributes_declares_text_and_binary_rules() -> None:
    text = (PROJECT_ROOT / ".gitattributes").read_text(encoding="utf-8")
    assert "* text=auto eol=lf" in text
    assert "*.ps1 text eol=crlf" in text
    assert "*.png binary" in text
    assert "*.zip binary" in text


def test_generated_and_migration_paths_are_forbidden() -> None:
    for path in (
        ".venv/Scripts/python.exe",
        ".venv-relocated-backup/pyvenv.cfg",
        "archive/migrations/checkpoint/file.py",
        "logs/release.log",
        "dist/iq4comm.whl",
        "ALPHA_PUBLIC_PREVIEW_13/apply.ps1",
        "CORE_OPTICS_02/payload/file.py",
        "showcase_output/index.html",
    ):
        assert is_forbidden_tracked_path(path)


def test_sensitive_paths_are_forbidden_but_examples_are_allowed() -> None:
    for path in (
        ".env",
        ".env.production",
        "credentials.json",
        "private/server.pem",
        "id_rsa",
    ):
        assert is_forbidden_tracked_path(path)
    assert not is_forbidden_tracked_path(".env.example")
    assert not is_forbidden_tracked_path("docs/security/example_token_format.md")


def test_normal_source_paths_are_allowed() -> None:
    for path in (
        "iqcore/states/coherent.py",
        "iq4comm/receivers/pnr.py",
        "tests/test_core_optics.py",
        "docs/release/checklist.md",
        ".github/workflows/ci.yml",
    ):
        assert not is_forbidden_tracked_path(path)


def test_oversized_file_is_reported(tmp_path: Path) -> None:
    path = tmp_path / "large.bin"
    path.write_bytes(b"0" * 64)
    errors, count, total_bytes = _file_errors(
        tmp_path,
        ["large.bin"],
        maximum_bytes=32,
    )
    assert count == 1
    assert total_bytes == 64
    assert errors and "size limit" in errors[0]


def test_repository_verifier_supports_source_snapshots_without_git() -> None:
    report = verify_repository(PROJECT_ROOT)
    assert report.healthy
    assert report.root == str(PROJECT_ROOT.resolve())
    assert isinstance(report.git_repository, bool)


def test_dependabot_covers_python_and_github_actions() -> None:
    text = (PROJECT_ROOT / ".github/dependabot.yml").read_text(encoding="utf-8")
    assert "package-ecosystem: pip" in text
    assert "package-ecosystem: github-actions" in text
    assert text.count("interval: weekly") == 2


def test_ci_and_release_candidate_run_repository_hygiene() -> None:
    ci = (PROJECT_ROOT / ".github/workflows/ci.yml").read_text(encoding="utf-8")
    release = (
        PROJECT_ROOT / ".github/workflows/release-candidate.yml"
    ).read_text(encoding="utf-8")
    command = "python tools/verify_repository_hygiene.py --root . --require-git"
    assert command in ci
    assert command in release
    assert "python -m build --wheel --sdist" in release
    assert "actions/upload-artifact@v4" in release


def test_repository_documentation_defines_remote_and_branch_protection() -> None:
    development = (
        PROJECT_ROOT / "docs/development/repository.md"
    ).read_text(encoding="utf-8")
    launch = (PROJECT_ROOT / "docs/release/github.md").read_text(encoding="utf-8")
    assert "iqcore must never import from `iq4comm`" in development
    assert "branch protection" in development.lower()
    assert "git remote add origin" in launch
    assert "private repository" in launch.lower()
    assert "GitHub Pages" in launch


def test_default_size_limit_is_reasonable_for_source_repository() -> None:
    assert DEFAULT_MAX_TRACKED_BYTES == 5 * 1024 * 1024


def test_source_manifest_includes_repository_governance_files() -> None:
    text = (PROJECT_ROOT / "MANIFEST.in").read_text(encoding="utf-8")
    assert "include GOVERNANCE.md" in text
    assert "include .gitignore" in text
    assert "recursive-include .github" in text
