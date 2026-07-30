"""Shared artifact helpers for the iQuant4 developer-alpha showcase."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def prepare_output_directory(path: str | Path) -> Path:
    """Create and return an absolute showcase output directory."""
    output_directory = Path(path).expanduser().resolve()
    output_directory.mkdir(parents=True, exist_ok=True)
    return output_directory


def write_json(path: str | Path, payload: Any) -> Path:
    """Write a JSON artifact with deterministic, readable formatting."""
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(payload, indent=2, sort_keys=True, default=str) + "\n",
        encoding="utf-8",
    )
    return output_path


def relative_artifact_path(path: Path, root: Path) -> str:
    """Return a portable artifact path relative to a showcase root."""
    return path.resolve().relative_to(root.resolve()).as_posix()


__all__ = [
    "prepare_output_directory",
    "relative_artifact_path",
    "write_json",
]
