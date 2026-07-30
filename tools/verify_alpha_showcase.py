"""Run a fast, headless verification of the flagship alpha showcase."""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from iq4comm.analysis.receiver_family import ReceiverFamilyConfiguration
from iq4comm.showcase import (
    LossyCatConfiguration,
    run_alpha_showcase,
)


def assert_png(path: Path) -> None:
    if not path.is_file() or path.stat().st_size < 100:
        raise RuntimeError(f"missing or empty PNG artifact: {path}")
    if path.read_bytes()[:8] != b"\x89PNG\r\n\x1a\n":
        raise RuntimeError(f"invalid PNG signature: {path}")


def main() -> None:
    with tempfile.TemporaryDirectory(prefix="iquant4_showcase_verify_") as temp:
        root = Path(temp)
        manifest = run_alpha_showcase(
            root,
            include_tomography=False,
            receiver_configuration=ReceiverFamilyConfiguration(
                distances_km=(0.0, 20.0),
                max_pnr_threshold=10,
                homodyne_threshold_step=0.5,
                heterodyne_threshold_step=0.5,
            ),
            lossy_cat_configuration=LossyCatConfiguration(
                alpha=1.0,
                cutoff=14,
                transmissivities=(1.0, 0.5),
                extent=4.0,
                grid_points=61,
            ),
        )
        manifest_path = Path(manifest["manifest_path"])
        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
        if payload["receiver_family"]["status"] != "completed":
            raise RuntimeError("receiver-family showcase did not complete")
        if payload["lossy_cat"]["status"] != "completed":
            raise RuntimeError("lossy-cat showcase did not complete")
        if payload["sign_free_tomography"]["status"] != "not-requested":
            raise RuntimeError("unexpected tomography status in fast verification")
        if payload["dashboard"]["status"] != "completed":
            raise RuntimeError("offline dashboard did not complete")

        for section in ("receiver_family", "lossy_cat", "dashboard"):
            for relative_path in payload[section]["artifacts"]:
                path = root / relative_path
                if not path.is_file() or path.stat().st_size == 0:
                    raise RuntimeError(f"missing showcase artifact: {path}")
                if path.suffix.lower() == ".png":
                    assert_png(path)

        dashboard_html = root / "index.html"
        standalone_html = root / "iQuant4_showcase_standalone.html"
        dashboard_data = root / "dashboard_data.json"
        for path in (dashboard_html, standalone_html, dashboard_data):
            if not path.is_file() or path.stat().st_size < 100:
                raise RuntimeError(f"missing dashboard artifact: {path}")
        html = dashboard_html.read_text(encoding="utf-8")
        if "iQuant4 Developer Alpha Showcase" not in html:
            raise RuntimeError("dashboard title is missing")
        if "http://" in html or "https://" in html:
            raise RuntimeError("dashboard contains an external network dependency")

    print("alpha showcase verification passed")


if __name__ == "__main__":
    main()
