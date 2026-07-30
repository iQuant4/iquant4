"""Verify wheel, source distribution, and an isolated installation."""

from __future__ import annotations

import sys
from pathlib import Path

from verify_clean_install import verify_clean_install
from verify_sdist import verify_sdist
from verify_wheel import verify_wheel


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("usage: verify_release_candidate.py <artifact-directory>")

    artifact_directory = Path(sys.argv[1]).resolve()
    wheels = sorted(artifact_directory.glob("iq4comm-*.whl"))
    sdists = sorted(artifact_directory.glob("iq4comm-*.tar.gz"))
    if len(wheels) != 1:
        raise RuntimeError(
            f"expected exactly one iq4comm wheel in {artifact_directory}; "
            f"found {len(wheels)}"
        )
    if len(sdists) != 1:
        raise RuntimeError(
            f"expected exactly one iq4comm sdist in {artifact_directory}; "
            f"found {len(sdists)}"
        )

    verify_wheel(wheels[0])
    verify_sdist(sdists[0])
    verify_clean_install(wheels[0])
    print("release candidate verification passed")


if __name__ == "__main__":
    main()
