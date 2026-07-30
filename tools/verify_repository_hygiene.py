"""Verify that the iQuant4 repository is safe, intentional, and release-ready."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from dataclasses import asdict, dataclass
from pathlib import Path, PurePosixPath
from typing import Iterable, Sequence


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MAX_TRACKED_BYTES = 5 * 1024 * 1024

REQUIRED_REPOSITORY_FILES = (
    ".gitattributes",
    ".gitignore",
    ".github/dependabot.yml",
    ".github/workflows/ci.yml",
    ".github/workflows/pages.yml",
    ".github/workflows/release-candidate.yml",
    "CHANGELOG.md",
    "CITATION.cff",
    "CODE_OF_CONDUCT.md",
    "CONTRIBUTING.md",
    "GOVERNANCE.md",
    "LICENSE",
    "README.md",
    "ROADMAP.md",
    "SECURITY.md",
    "docs/development/repository.md",
    "docs/release/github.md",
    "pyproject.toml",
)

REQUIRED_GITIGNORE_PATTERNS = (
    ".venv/",
    ".venv-*/",
    "archive/",
    "logs/",
    "build/",
    "dist/",
    "*.egg-info/",
    "/ALPHA_*/",
    "/ARCHITECTURE_*/",
    "/COMM_*/",
    "/CORE_*/",
    "/showcase_output/",
    "/documentation_output/",
    "/public_preview/",
    ".env",
    "*.pem",
    "*.key",
)

FORBIDDEN_TRACKED_PREFIXES = (
    ".venv/",
    ".venv-",
    ".pytest_cache/",
    "__pycache__/",
    "archive/",
    "build/",
    "dist/",
    "logs/",
    "showcase_output/",
    "documentation_output/",
    "public_preview/",
    "Data/",
    "Figures/",
    "Notebooks/",
    "ALPHA_",
    "ARCHITECTURE_",
    "COMM_",
    "CORE_",
)

FORBIDDEN_TRACKED_SUFFIXES = (
    ".pyc",
    ".pyo",
    ".whl",
    ".zip",
    ".log",
    ".pem",
    ".key",
    ".p12",
    ".pfx",
    ".sqlite",
    ".sqlite3",
)

SENSITIVE_BASENAMES = {
    ".env",
    ".env.local",
    ".env.production",
    "credentials.json",
    "secrets.json",
    "token.json",
    "id_rsa",
    "id_ed25519",
}

ALLOWED_SENSITIVE_EXAMPLES = {
    ".env.example",
    ".env.template",
}


@dataclass(frozen=True)
class RepositoryReport:
    root: str
    git_repository: bool
    branch: str | None
    inspected_file_count: int
    inspected_bytes: int
    clean: bool | None
    errors: tuple[str, ...]
    warnings: tuple[str, ...]

    @property
    def healthy(self) -> bool:
        return not self.errors


def _run_git(root: Path, arguments: Sequence[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *arguments],
        cwd=root,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )


def _normalize_path(path: str | Path) -> str:
    value = str(path).replace("\\", "/")
    while value.startswith("./"):
        value = value[2:]
    return value.lstrip("/")


def is_forbidden_tracked_path(path: str | Path) -> bool:
    """Return True when a path must never be committed to the repository."""
    normalized = _normalize_path(path)
    lowered = normalized.lower()
    basename = PurePosixPath(normalized).name.lower()

    if basename in ALLOWED_SENSITIVE_EXAMPLES:
        return False
    if basename in SENSITIVE_BASENAMES:
        return True
    if basename.startswith(".env."):
        return True

    for prefix in FORBIDDEN_TRACKED_PREFIXES:
        normalized_prefix = _normalize_path(prefix)
        if normalized.startswith(normalized_prefix):
            return True
        if normalized_prefix.endswith("-") and normalized.startswith(normalized_prefix):
            return True

    return lowered.endswith(FORBIDDEN_TRACKED_SUFFIXES)


def _required_file_errors(root: Path) -> list[str]:
    return [
        f"required repository file is missing: {relative_path}"
        for relative_path in REQUIRED_REPOSITORY_FILES
        if not (root / relative_path).is_file()
    ]


def _gitignore_errors(root: Path) -> list[str]:
    path = root / ".gitignore"
    if not path.is_file():
        return [".gitignore is missing"]
    text = path.read_text(encoding="utf-8")
    return [
        f".gitignore is missing required pattern: {pattern}"
        for pattern in REQUIRED_GITIGNORE_PATTERNS
        if pattern not in text
    ]


def _git_file_list(root: Path, *, staged: bool) -> tuple[list[str], list[str]]:
    if staged:
        result = _run_git(
            root,
            ["diff", "--cached", "--name-only", "--diff-filter=ACMR", "-z"],
        )
    else:
        result = _run_git(root, ["ls-files", "-z"])
    if result.returncode != 0:
        return [], [result.stderr.strip() or "git could not list repository files"]
    return [value for value in result.stdout.split("\0") if value], []


def _file_errors(
    root: Path,
    paths: Iterable[str],
    *,
    maximum_bytes: int,
) -> tuple[list[str], int, int]:
    errors: list[str] = []
    count = 0
    total_bytes = 0
    for relative_path in paths:
        count += 1
        normalized = _normalize_path(relative_path)
        if is_forbidden_tracked_path(normalized):
            errors.append(f"forbidden path is tracked or staged: {normalized}")
            continue

        full_path = root / Path(normalized)
        if not full_path.is_file():
            continue
        size = full_path.stat().st_size
        total_bytes += size
        if size > maximum_bytes:
            errors.append(
                "tracked file exceeds the repository size limit "
                f"({size} > {maximum_bytes} bytes): {normalized}"
            )
    return errors, count, total_bytes


def verify_repository(
    root: Path,
    *,
    staged: bool = False,
    require_git: bool = False,
    require_main: bool = False,
    require_clean: bool = False,
    maximum_bytes: int = DEFAULT_MAX_TRACKED_BYTES,
) -> RepositoryReport:
    """Inspect repository policy, tracked files, branch, and working-tree state."""
    root = root.resolve()
    errors = _required_file_errors(root)
    errors.extend(_gitignore_errors(root))
    warnings: list[str] = []

    git_repository = (root / ".git").exists()
    branch: str | None = None
    clean: bool | None = None
    inspected_paths: list[str] = []

    if not git_repository:
        if require_git:
            errors.append("Git repository is required but .git was not found")
        else:
            warnings.append("Git repository is not initialized; file-index checks were skipped")
    else:
        branch_result = _run_git(root, ["branch", "--show-current"])
        if branch_result.returncode == 0:
            branch = branch_result.stdout.strip() or None
        else:
            errors.append(branch_result.stderr.strip() or "Git branch could not be read")

        if require_main and branch != "main":
            errors.append(f"expected current branch 'main', found {branch!r}")

        inspected_paths, git_errors = _git_file_list(root, staged=staged)
        errors.extend(git_errors)

        status_result = _run_git(root, ["status", "--porcelain", "--untracked-files=all"])
        if status_result.returncode == 0:
            clean = not bool(status_result.stdout.strip())
        else:
            errors.append(status_result.stderr.strip() or "Git status could not be read")
        if require_clean and clean is not True:
            errors.append("working tree is not clean")

    file_errors, count, total_bytes = _file_errors(
        root,
        inspected_paths,
        maximum_bytes=maximum_bytes,
    )
    errors.extend(file_errors)

    return RepositoryReport(
        root=str(root),
        git_repository=git_repository,
        branch=branch,
        inspected_file_count=count,
        inspected_bytes=total_bytes,
        clean=clean,
        errors=tuple(errors),
        warnings=tuple(warnings),
    )


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Verify iQuant4 Git repository hygiene and release policy."
    )
    parser.add_argument("--root", type=Path, default=PROJECT_ROOT)
    parser.add_argument("--staged", action="store_true")
    parser.add_argument("--require-git", action="store_true")
    parser.add_argument("--require-main", action="store_true")
    parser.add_argument("--require-clean", action="store_true")
    parser.add_argument(
        "--max-bytes",
        type=int,
        default=DEFAULT_MAX_TRACKED_BYTES,
    )
    parser.add_argument("--json", action="store_true")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    report = verify_repository(
        args.root,
        staged=args.staged,
        require_git=args.require_git,
        require_main=args.require_main,
        require_clean=args.require_clean,
        maximum_bytes=args.max_bytes,
    )

    if args.json:
        payload = asdict(report)
        payload["healthy"] = report.healthy
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print("iQuant4 Repository Hygiene")
        print("===========================")
        print(f"Root          : {report.root}")
        print(f"Git repository: {report.git_repository}")
        print(f"Branch        : {report.branch or 'N/A'}")
        print(f"Files checked : {report.inspected_file_count}")
        print(f"Bytes checked : {report.inspected_bytes}")
        print(f"Clean tree    : {report.clean if report.clean is not None else 'N/A'}")
        for warning in report.warnings:
            print(f"WARNING       : {warning}")
        for error in report.errors:
            print(f"ERROR         : {error}")
        print(f"Status        : {'HEALTHY' if report.healthy else 'FAILED'}")

    return 0 if report.healthy else 1


if __name__ == "__main__":
    raise SystemExit(main())
