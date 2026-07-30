"""Smoke-test the developer-alpha user experience."""

from __future__ import annotations

import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from iq4comm.analysis import (
    ReceiverFamilyConfiguration,
    compare_receiver_families,
    format_receiver_family_report,
)


def main() -> None:
    config = ReceiverFamilyConfiguration(
        distances_km=(0.0, 20.0),
        max_pnr_threshold=10,
        homodyne_threshold_step=0.25,
        heterodyne_threshold_step=0.25,
    )
    rows = compare_receiver_families(config)
    report = format_receiver_family_report(rows, config)

    assert len(rows) == 2
    assert rows[0].winner == "PNR"
    assert rows[1].winner == "Homodyne"
    assert report.startswith("iQuant4Comm Receiver-Family Comparison")

    print("alpha experience smoke test passed")
    print("winners:", ", ".join(row.winner for row in rows))


if __name__ == "__main__":
    main()
