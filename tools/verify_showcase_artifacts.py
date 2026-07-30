"""Verify a generated iQuant4 showcase artifact directory."""

from __future__ import annotations

import json
import sys
from pathlib import Path


def verify_showcase_artifacts(root: Path, *, require_tomography: bool) -> None:
    root = root.resolve()
    manifest_path = root / "showcase_manifest.json"
    if not manifest_path.is_file():
        raise RuntimeError(f"showcase manifest is missing: {manifest_path}")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    for section in ("receiver_family", "lossy_cat", "sign_free_tomography", "dashboard"):
        if section not in manifest:
            raise RuntimeError(f"showcase manifest is missing section: {section}")

    if manifest["receiver_family"].get("status") != "completed":
        raise RuntimeError("receiver-family showcase did not complete")
    if manifest["lossy_cat"].get("status") != "completed":
        raise RuntimeError("lossy-cat showcase did not complete")
    if manifest["dashboard"].get("status") != "completed":
        raise RuntimeError("offline dashboard did not complete")

    tomography_status = manifest["sign_free_tomography"].get("status")
    if require_tomography and tomography_status != "completed":
        raise RuntimeError(
            f"tomography was required but reported status {tomography_status!r}"
        )

    for section in ("receiver_family", "lossy_cat", "sign_free_tomography", "dashboard"):
        for relative_path in manifest[section].get("artifacts", []):
            path = root / relative_path
            if not path.is_file() or path.stat().st_size == 0:
                raise RuntimeError(f"missing or empty showcase artifact: {path}")
            if path.suffix.lower() == ".png":
                if path.read_bytes()[:8] != b"\x89PNG\r\n\x1a\n":
                    raise RuntimeError(f"invalid PNG showcase artifact: {path}")

    dashboard_html = root / "index.html"
    standalone_html = root / "iQuant4_showcase_standalone.html"
    dashboard_data = root / "dashboard_data.json"
    for path in (dashboard_html, standalone_html, dashboard_data):
        if not path.is_file() or path.stat().st_size < 100:
            raise RuntimeError(f"missing or empty dashboard artifact: {path}")
    html = dashboard_html.read_text(encoding="utf-8")
    if "iQuant4 Developer Alpha Showcase" not in html:
        raise RuntimeError("dashboard title is missing")
    if "http://" in html or "https://" in html:
        raise RuntimeError("dashboard contains an external network dependency")

    if require_tomography:
        fidelity = manifest["sign_free_tomography"].get("fidelity")
        if fidelity is None or not 0.0 <= float(fidelity) <= 1.0:
            raise RuntimeError("tomography fidelity is missing or invalid")

    print("showcase artifacts passed")
    print(manifest_path)


def main() -> None:
    if len(sys.argv) not in {2, 3}:
        raise SystemExit(
            "usage: verify_showcase_artifacts.py <showcase-directory> "
            "[--require-tomography]"
        )
    require_tomography = len(sys.argv) == 3
    if require_tomography and sys.argv[2] != "--require-tomography":
        raise SystemExit(f"unknown option: {sys.argv[2]}")
    verify_showcase_artifacts(
        Path(sys.argv[1]),
        require_tomography=require_tomography,
    )


if __name__ == "__main__":
    main()
