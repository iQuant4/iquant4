"""Multi-span long-haul link demo for the iQuant4 platform.

Builds a chain of 80 km SMF-28 spans, each followed by an EDFA that exactly
compensates the span loss, and reports OSNR versus reach -- plus the end-to-end
transmissivity the quantum branch would use for a QKD key-rate analysis.

Run:
    python -m examples.multispan_link_demo
"""

from __future__ import annotations

import numpy as np

from iqcore.fiber import Amplifier, Link, SMF28


def build_link(n_spans: int, span_km: float = 80.0,
               noise_figure_db: float = 5.0) -> Link:
    link = Link()
    gain_db = SMF28.loss_db(span_km)
    for _ in range(n_spans):
        link.span(SMF28, span_km).amplifier(
            Amplifier(gain_db=gain_db, noise_figure_db=noise_figure_db))
    return link


def main() -> None:
    launch_dbm = 0.0
    launch_w = 1e-3 * 10 ** (launch_dbm / 10.0)
    print(f"Chain of 80 km SMF-28 spans, EDFA NF = 5 dB, launch = {launch_dbm:.0f} dBm\n")
    print(f"{'spans':>6} {'reach_km':>9} {'OSNR_dB':>9} {'net_dB':>8} "
          f"{'eta_passive':>13}")
    for n in (1, 2, 4, 8, 12, 16, 20):
        link = build_link(n)
        print(f"{n:>6} {link.total_length_km:>9.0f} {link.osnr_db(launch_w):>9.2f} "
              f"{link.net_gain_db:>8.2f} {link.passive_transmissivity:>13.2e}")

    # Reach at a representative OSNR threshold (e.g. 15 dB for coherent QPSK).
    threshold_db = 15.0
    n = 1
    while build_link(n).osnr_db(launch_w) > threshold_db and n < 1000:
        n += 1
    reach = build_link(n - 1)
    print(f"\nReach at OSNR >= {threshold_db:.0f} dB: "
          f"{reach.total_length_km:.0f} km ({n - 1} spans)")


if __name__ == "__main__":
    main()
