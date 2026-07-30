"""Validate the contents of an iQuant4 source distribution."""

from __future__ import annotations

import sys
import tarfile
from pathlib import Path


REQUIRED_SUFFIXES = {
    "LICENSE",
    "README.md",
    "CHANGELOG.md",
    "CONTRIBUTING.md",
    "SECURITY.md",
    "CITATION.cff",
    "ROADMAP.md",
    "CODE_OF_CONDUCT.md",
    "pyproject.toml",
    "iqcore/__init__.py",
    "iq4comm/__init__.py",
    "docs/release/public_api.md",
    "docs/release/checklist.md",
    "docs/release/validation.md",
    "examples/alpha_quickstart.py",
    "examples/showcase/run_alpha_showcase.py",
    "docs/tutorials/alpha_showcase.md",
    "docs/release/showcase.md",
    "docs/release/dashboard.md",
    "docs/release/documentation.md",
    "docs/release/public_preview.md",
    ".github/workflows/pages.yml",
    "docs/tutorials/showcase_dashboard.md",
    "examples/showcase/build_dashboard.py",
}

FORBIDDEN_PARTS = {
    ".venv",
    ".pytest_cache",
    "__pycache__",
    "archive",
    "logs",
    "build",
    "dist",
}


def verify_sdist(path: Path) -> None:
    archive_path = path.resolve()
    if not archive_path.is_file():
        raise FileNotFoundError(archive_path)

    with tarfile.open(archive_path, "r:gz") as archive:
        names = {member.name.replace("\\", "/") for member in archive.getmembers()}

    def has_suffix(suffix: str) -> bool:
        return any(name == suffix or name.endswith("/" + suffix) for name in names)

    missing = sorted(suffix for suffix in REQUIRED_SUFFIXES if not has_suffix(suffix))
    if missing:
        raise RuntimeError(f"sdist is missing required files: {missing}")

    forbidden = sorted(
        name
        for name in names
        if any(part in FORBIDDEN_PARTS for part in Path(name).parts)
        or name.endswith("requirements-lock.txt")
        or "ALPHA_RELEASE_GATE_09" in name
    )
    if forbidden:
        raise RuntimeError(f"sdist contains local-only files: {forbidden[:20]}")

    print("sdist contents passed")
    print(archive_path)


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("usage: verify_sdist.py <sdist-path>")
    verify_sdist(Path(sys.argv[1]))


if __name__ == "__main__":
    main()
