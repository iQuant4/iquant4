"""Build and validate the static iQuant4 public-preview portal."""

from __future__ import annotations

import json
from pathlib import Path
import tempfile
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from iq4comm.portal import build_public_preview


def verify_public_preview() -> None:
    """Generate a docs-only preview and validate portable artifacts."""
    with tempfile.TemporaryDirectory(prefix="iquant4_public_preview_") as temp:
        output = Path(temp) / "public_preview"
        result = build_public_preview(output, include_showcase=False)
        required = (
            result.index_path,
            result.manifest_path,
            output / "roadmap.html",
            output / "404.html",
            output / "portal.css",
            output / "portal.js",
            output / "docs" / "index.html",
            output / ".nojekyll",
        )
        if any(not path.is_file() for path in required):
            raise RuntimeError("public preview is missing required artifacts")

        manifest = json.loads(result.manifest_path.read_text(encoding="utf-8"))
        if not manifest.get("offline_ready"):
            raise RuntimeError("public preview is not marked offline-ready")
        if not manifest.get("static_hosting_ready"):
            raise RuntimeError("public preview is not marked static-hosting-ready")
        if manifest.get("active_packages") != ["iqcore", "iq4comm"]:
            raise RuntimeError("public preview active-package metadata is invalid")

        html = result.index_path.read_text(encoding="utf-8")
        for marker in (
            "iQuant4",
            "iqcore",
            "iQuant4Comm",
            "Solutions",
            "Convenience",
            "Experiences",
            "Developer-alpha scope",
        ):
            if marker not in html:
                raise RuntimeError(f"public preview is missing marker: {marker}")
        if "http://" in html or "https://" in html:
            raise RuntimeError("public preview requires external assets")

    print("public preview verification passed")


def main() -> None:
    verify_public_preview()


if __name__ == "__main__":
    main()
