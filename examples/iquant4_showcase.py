"""iQuant4 capstone showcase -- the whole platform, end to end.

Runs one physical fiber description through every layer of the stack and prints
a narrative summary:

    fiber propagation (NLSE)  ->  multi-span link + OSNR  ->  GN model + reach
      ->  coherent BER  ->  digital backpropagation  ->  DV & CV QKD
      ->  classical-quantum DWDM coexistence (the differentiator)

Because it exercises iqcore.fiber and every iq4comm subpackage together, a clean
run is also a full-stack integration check.

Run:
    python -m examples.iquant4_showcase
"""

from __future__ import annotations

import numpy as np

from iqcore.fiber import (
    SMF28, TimeGrid, gaussian_pulse, propagate, backpropagate,
    compensate_dispersion, nmse, Amplifier, Link, DWDMGrid,
)
from iq4comm.dsp import ber_theory, monte_carlo_ber, gn_operating_point
from iq4comm.qkd import (
    bb84_rate_vs_distance, cvqkd_rate_vs_distance,
    coexistence_curve, coexistence_cv_key_rate, coexistence_dv_key_rate,
)

RULE = "=" * 66


def section(title: str) -> None:
    print(f"\n{RULE}\n  {title}\n{RULE}")


def main() -> None:
    print("\n" + RULE + "\n  iQuant4 -- optical & quantum communication platform\n" + RULE)

    # 1. Fiber propagation (the shared NLSE foundation) -----------------
    section("1  Fiber propagation (NLSE, split-step Fourier)")
    grid = TimeGrid(4096, 0.5)
    pulse = gaussian_pulse(grid, peak_power_w=1e-3, width_ps=12.0)
    res = propagate(pulse, grid, SMF28, length_km=80.0)
    print(f"  80 km SMF-28: measured loss = {res.loss_db:.2f} dB "
          f"(expected {SMF28.loss_db(80.0):.2f} dB), {res.num_steps} steps")

    # 2. Multi-span link + OSNR ----------------------------------------
    section("2  Multi-span link + OSNR")
    link = Link()
    for _ in range(10):
        link.span(SMF28, 80.0).amplifier(
            Amplifier(gain_db=SMF28.loss_db(80.0), noise_figure_db=5.0))
    print(f"  {link!r}: OSNR = {link.osnr_db(1e-3):.2f} dB at 0 dBm launch, "
          f"passive transmissivity = {link.passive_transmissivity:.2e}")

    # 3. GN model + reach ----------------------------------------------
    section("3  GN model -- nonlinear reach")
    amp = Amplifier(gain_db=SMF28.loss_db(80.0), noise_figure_db=5.0)
    op = gn_operating_point(SMF28, 80.0, 12, amp, 32e9, 40 * 50e9)
    print(f"  40x50GHz DWDM: optimal launch {op.optimal_launch_dbm:.1f} dBm, "
          f"peak SNR {op.max_snr_db:.1f} dB at {op.total_length_km:.0f} km")

    # 4. Coherent BER (theory vs Monte-Carlo) --------------------------
    section("4  Coherent BER")
    rng = np.random.default_rng(0)
    for fmt, ebn0 in [("QPSK", 8.0), ("16QAM", 12.0)]:
        mc = monte_carlo_ber(fmt, ebn0, num_bits=1_000_000, rng=rng).ber
        print(f"  {fmt:>6} @ {ebn0:.0f} dB Eb/N0: theory {ber_theory(fmt, ebn0):.2e}, "
              f"simulated {mc:.2e}")

    # 5. Digital backpropagation ---------------------------------------
    section("5  Nonlinear compensation (digital backpropagation)")
    hp = gaussian_pulse(grid, peak_power_w=80e-3, width_ps=10.0)
    fwd = propagate(hp, grid, SMF28, 80.0)
    cd = compensate_dispersion(fwd.field, grid, SMF28, 80.0) / np.sqrt(SMF28.transmissivity(80.0))
    dbp = backpropagate(fwd.field, grid, SMF28, 80.0).field
    print(f"  80 km @ 19 dBm: linear-EQ NMSE {nmse(cd, hp):.2e}  ->  "
          f"DBP NMSE {nmse(dbp, hp):.2e}")

    # 6. QKD -- both protocols -----------------------------------------
    section("6  Quantum key distribution (DV + CV)")
    d = np.arange(0, 320, 2.0)
    dv = bb84_rate_vs_distance(d)
    cv = cvqkd_rate_vs_distance(d, excess_noise=0.02)
    print(f"  DV-QKD (BB84 decoy): secure to {d[np.max(np.where(dv > 0))]:.0f} km")
    print(f"  CV-QKD (GG02 homodyne): secure to {d[np.max(np.where(cv > 0))]:.0f} km")

    # 7. Coexistence -- the differentiator -----------------------------
    section("7  QKD-classical DWDM coexistence  [the differentiator]")
    grid_dbm = np.arange(-20, 8, 0.5)
    pts = coexistence_curve(50.0, 20, grid_dbm)
    secure = [p for p in pts if p.secure]
    max_secure = max(p.launch_dbm for p in secure)
    cap_at_edge = next(p.classical_capacity_bps for p in pts
                       if abs(p.launch_dbm - max_secure) < 1e-9)
    print(f"  20-channel DWDM + QKD @ 50 km on ONE fiber model:")
    print(f"    secure up to {max_secure:.1f} dBm/channel classical launch")
    print(f"    classical capacity at that edge: {cap_at_edge / 1e12:.1f} Tb/s")
    print(f"    key rate there -- DV: {coexistence_dv_key_rate(50, max_secure, 20):.2e}, "
          f"CV: {coexistence_cv_key_rate(50, max_secure, 20):.2e} (CV ~5x higher)")

    print("\n" + RULE)
    print("  One FiberSpec drove classical capacity, DV-QKD, CV-QKD, and their")
    print("  coexistence -- the unification no existing tool packages.")
    print(RULE + "\n")


if __name__ == "__main__":
    main()
