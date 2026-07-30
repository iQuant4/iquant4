"""Run a fast verification of the offline iQuant4 showcase dashboard."""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from iq4comm.analysis.receiver_family import ReceiverFamilyConfiguration
from iq4comm.showcase import LossyCatConfiguration, run_alpha_showcase


def main() -> None:
    with tempfile.TemporaryDirectory(prefix="iquant4_dashboard_verify_") as temp:
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
        dashboard = root / "index.html"
        standalone = root / "iQuant4_showcase_standalone.html"
        data_path = root / "dashboard_data.json"
        for path in (dashboard, standalone, data_path):
            if not path.is_file() or path.stat().st_size < 100:
                raise RuntimeError(f"missing dashboard artifact: {path}")

        html = dashboard.read_text(encoding="utf-8")
        if "iQuant4 Developer Alpha Showcase" not in html:
            raise RuntimeError("dashboard title is missing")
        if "http://" in html or "https://" in html:
            raise RuntimeError("dashboard contains external network assets")
        if standalone.read_text(encoding="utf-8").count("data:image/png;base64,") < 2:
            raise RuntimeError("standalone dashboard did not embed the figures")

        data = json.loads(data_path.read_text(encoding="utf-8"))
        if data["receiver_family"]["distance_count"] != 2:
            raise RuntimeError("dashboard receiver summary is incomplete")
        if data["sign_free_tomography"]["status"] != "not-requested":
            raise RuntimeError("dashboard tomography status is incorrect")
        if Path(manifest["dashboard_path"]).resolve() != dashboard.resolve():
            raise RuntimeError("returned dashboard path is incorrect")

    print("showcase dashboard verification passed")


if __name__ == "__main__":
    main()
