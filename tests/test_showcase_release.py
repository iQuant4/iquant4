from __future__ import annotations

from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:  # Python 3.10
    import tomli as tomllib


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_showcase_files_are_documented_and_packaged() -> None:
    required = (
        "iq4comm/showcase/__init__.py",
        "iq4comm/showcase/cli.py",
        "iq4comm/showcase/dashboard.py",
        "iq4comm/showcase/receiver_family.py",
        "iq4comm/showcase/lossy_cat.py",
        "iq4comm/showcase/tomography.py",
        "examples/showcase/run_alpha_showcase.py",
        "docs/tutorials/alpha_showcase.md",
        "docs/release/showcase.md",
        "docs/release/dashboard.md",
        "docs/tutorials/showcase_dashboard.md",
        "examples/showcase/build_dashboard.py",
    )
    assert all((PROJECT_ROOT / path).is_file() for path in required)


def test_readme_exposes_one_command_showcase() -> None:
    readme = (PROJECT_ROOT / "README.md").read_text(encoding="utf-8")
    assert "iq4comm showcase all" in readme
    assert "alpha_showcase.md" in readme
    assert "showcase_dashboard.md" in readme
    assert "index.html" in readme


def test_public_api_documents_showcase_functions() -> None:
    public_api = (PROJECT_ROOT / "docs/release/public_api.md").read_text(
        encoding="utf-8"
    )
    assert "run_alpha_showcase" in public_api
    assert "run_lossy_cat_showcase" in public_api
    assert "run_sign_free_tomography_showcase" in public_api
    assert "build_showcase_dashboard" in public_api
    assert "open_showcase_dashboard" in public_api


def test_showcase_release_gate_maps_to_product_roadmap() -> None:
    document = (PROJECT_ROOT / "docs/release/showcase.md").read_text(
        encoding="utf-8"
    )
    for term in ("Solutions", "Convenience", "Experience"):
        assert term in document


def test_project_dependencies_cover_showcase_runtime() -> None:
    metadata = tomllib.loads(
        (PROJECT_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    )["project"]
    dependencies = "\n".join(metadata["dependencies"])
    assert "numpy" in dependencies
    assert "matplotlib" in dependencies
    assert "cvxpy" in "\n".join(metadata["optional-dependencies"]["tomography"])


def test_gitignore_excludes_default_showcase_output() -> None:
    gitignore = (PROJECT_ROOT / ".gitignore").read_text(encoding="utf-8")
    assert "/showcase_output/" in gitignore
