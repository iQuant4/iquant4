"""Validate the contents and console entry points of an iQuant4 wheel."""

from __future__ import annotations

import sys
from pathlib import Path
from zipfile import ZipFile


def verify_wheel(wheel_path: Path) -> None:
    """Validate required package files and console entry points."""
    wheel = wheel_path.resolve()
    if not wheel.is_file():
        raise FileNotFoundError(wheel)

    with ZipFile(wheel) as archive:
        names = set(archive.namelist())

    required = {
        "iqcore/__init__.py",
        "iqcore/states/__init__.py",
        "iqcore/measurements/quadrature.py",
        "iqcore/tomography/sign_free.py",
        "iq4comm/__init__.py",
        "iq4comm/__main__.py",
        "iq4comm/cli.py",
        "iq4comm/diagnostics.py",
        "iq4comm/receivers/homodyne.py",
        "iq4comm/receivers/heterodyne.py",
        "iq4comm/receivers/pnr.py",
        "iq4comm/analysis/receiver_family.py",
        "iq4comm/showcase/cli.py",
        "iq4comm/showcase/dashboard.py",
        "iq4comm/showcase/lossy_cat.py",
        "iq4comm/showcase/receiver_family.py",
        "iq4comm/showcase/tomography.py",
        "iq4comm/portal/__init__.py",
        "iq4comm/portal/cli.py",
        "iq4comm/portal/site.py",
    }
    missing = sorted(required - names)
    if missing:
        raise RuntimeError(f"wheel is missing required files: {missing}")

    entry_point_files = [
        name for name in names if name.endswith(".dist-info/entry_points.txt")
    ]
    if len(entry_point_files) != 1:
        raise RuntimeError(
            "wheel must contain exactly one dist-info entry_points.txt"
        )

    with ZipFile(wheel) as archive:
        entry_points = archive.read(entry_point_files[0]).decode("utf-8")

    expected_entries = {
        "iq4comm = iq4comm.cli:main",
        "iq4comm-receiver-family = iq4comm.analysis.receiver_family:main",
    }
    missing_entries = sorted(
        entry for entry in expected_entries if entry not in entry_points
    )
    if missing_entries:
        raise RuntimeError(
            f"wheel is missing console entry points: {missing_entries}"
        )

    metadata_files = [
        name for name in names if name.endswith(".dist-info/METADATA")
    ]
    license_files = [
        name for name in names if name.endswith(".dist-info/licenses/LICENSE")
    ]
    if len(metadata_files) != 1:
        raise RuntimeError("wheel must contain exactly one METADATA file")
    if len(license_files) != 1:
        raise RuntimeError("wheel must contain exactly one packaged LICENSE file")

    with ZipFile(wheel) as archive:
        metadata_text = archive.read(metadata_files[0]).decode("utf-8")
        license_text = archive.read(license_files[0]).decode("utf-8")

    if "License-Expression: Apache-2.0" in metadata_text:
        if "Apache License" not in license_text:
            raise RuntimeError("wheel license text does not match Apache-2.0 metadata")
    elif "License-Expression: MIT" in metadata_text:
        if "Permission is hereby granted" not in license_text:
            raise RuntimeError("wheel license text does not match MIT metadata")
    else:
        raise RuntimeError("wheel is missing an approved License-Expression")

    print("wheel contents passed")
    print(wheel)


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("usage: verify_wheel.py <wheel-path>")
    verify_wheel(Path(sys.argv[1]))


if __name__ == "__main__":
    main()
