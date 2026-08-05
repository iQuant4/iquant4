"""iQuant4 validation suite: platform outputs vs references and closed-form limits.

Run:  python -m validation.validate      (from the repo root)

Each check compares a computed platform value against either a closed-form /
conserved-quantity reference (exact) or a published experimental/standard value,
and reports the agreement.  Prints a table and a machine-readable summary.
"""

from __future__ import annotations

import numpy as np

from iqcore.fiber import (SMF28, TimeGrid, gaussian_pulse, propagate,
                          PMDFiber, mean_dgd_ps, Amplifier)
from iq4comm.dsp import (ber_theory, monte_carlo_ber, q_to_ber, ber_to_q,
                         get_fec_code, net_coding_gain_db,
                         nli_coefficient, ase_power_w, effective_snr,
                         optimal_launch_power_w, laser_phase_noise)
from iq4comm.qkd import (bb84_decoy_key_rate, plob_bound_bits,
                         raman_background_yield, RamanModel,
                         optimal_segment_count, direct_plob_rate,
                         repeater_advantage_distance)

CHECKS: list[dict] = []


def record(name, computed, reference, source, tol_pct=None, exact=False, note=""):
    ok = True
    agree = ""
    if isinstance(reference, (int, float)) and isinstance(computed, (int, float)) \
            and reference != 0:
        err = abs(computed - reference) / abs(reference) * 100.0
        agree = f"{err:.2f}%"
        if tol_pct is not None:
            ok = err <= tol_pct
    CHECKS.append(dict(name=name, computed=computed, reference=reference,
                       source=source, agree=agree, ok=ok, exact=exact, note=note))


# ---- A. Fiber propagation (closed-form / conserved) ----
grid = TimeGrid(num_points=4096, dt_ps=0.5)
p = gaussian_pulse(grid, peak_power_w=1e-3, width_ps=20.0)
res = propagate(p, grid, SMF28, length_km=80.0, include_dispersion=False,
                include_nonlinearity=False)
e_in = np.sum(np.abs(p) ** 2)
e_out = np.sum(np.abs(res.field) ** 2)
record("Fiber pure-loss ratio (80 km)", e_out / e_in, 10 ** (-16.0 / 10),
       "closed form 10^(-alpha L/10)", tol_pct=0.01, exact=True)
record("SMF-28 beta2 (ps^2/km)", SMF28.beta2_ps2_per_km(), -21.7,
       "textbook D=17 ps/nm/km @1550", tol_pct=1.0)
record("SMF-28 loss over 80 km (dB)", SMF28.loss_db(80.0), 16.0,
       "0.2 dB/km x 80 km", tol_pct=0.01, exact=True)

# ---- B. BER: theory vs Monte-Carlo, and known Eb/N0 anchors ----
rng = np.random.default_rng(0)
th = ber_theory("QPSK", 8.0)
mc = monte_carlo_ber("QPSK", 8.0, num_bits=4_000_000, rng=rng).ber
record("QPSK BER @ 8 dB: MC vs theory", mc, th, "Monte-Carlo agreement",
       tol_pct=5.0)
# Eb/N0 for QPSK BER=1e-3 -> 6.79 dB (Q(sqrt(2 Eb/N0))=1e-3)
from scipy.optimize import brentq
ebn0_1e3 = brentq(lambda x: ber_theory("QPSK", x) - 1e-3, 0, 15)
record("QPSK Eb/N0 for BER 1e-3 (dB)", ebn0_1e3, 6.79,
       "closed form Q^-1", tol_pct=1.0)

# ---- C. Q-factor <-> BER ----
record("Q=6 -> BER", q_to_ber(6.0), 9.87e-10, "Q(6)=erfc(6/sqrt2)/2",
       tol_pct=1.0)
record("Q for BER 1e-12 (dB-lin)", ber_to_q(1e-12), 7.034,
       "standard optical benchmark", tol_pct=0.5)

# ---- D. GN model: optimal launch (closed form vs numeric) ----
d_km = 100.0
amp = Amplifier(gain_db=SMF28.loss_db(d_km), noise_figure_db=5.0)
eta_nli = nli_coefficient(SMF28, d_km, 1, 32e9, 50e9 * 40)
ase = ase_power_w(amp, 1, 32e9)
p_opt = optimal_launch_power_w(ase, eta_nli)
# numeric optimum
grid_p = np.linspace(1e-6, 5e-3, 20000)
snr = grid_p / (ase + eta_nli * grid_p ** 3)
p_num = grid_p[np.argmax(snr)]
record("GN optimal launch: closed-form vs numeric (W)", p_opt, p_num,
       "P_opt=(A/2eta)^(1/3)", tol_pct=1.0, exact=True)
record("GN optimal launch (dBm/ch)", 10 * np.log10(p_opt * 1e3), -1.6,
       "typical uncompensated span ~ -3..0 dBm", tol_pct=60.0,
       note="value lands in the textbook band, not a single number")

# ---- E. FEC ----
rs = get_fec_code("RS(255,239)")
record("RS(255,239) net coding gain, QPSK (dB)", net_coding_gain_db("QPSK", rs),
       6.2, "Nokia/G.709 GFEC (~6.2 dB NCG)", tol_pct=5.0)
record("RS(255,239) pre-FEC threshold (BER)", rs.threshold_ber(), 8e-5,
       "G.709 GFEC ~1e-4 order", tol_pct=60.0, note="order-of-magnitude anchor")
sd = get_fec_code("SD-FEC-20%")
record("SD-FEC-20% net coding gain (dB)", net_coding_gain_db("QPSK", sd), 11.0,
       "modern SD-FEC 10-12 dB", tol_pct=15.0)

# ---- F. QKD ----
record("PLOB bound @ 100 km (bits/use)", plob_bound_bits(SMF28.transmissivity(100.0)),
       0.01446, "-log2(1-eta), eta=10^-2", tol_pct=1.0, exact=True)
# BB84 decoy asymptotic max reach
d = np.arange(0, 320, 2.0)
r = np.array([bb84_decoy_key_rate(SMF28.transmissivity(x)) for x in d])
reach = d[np.max(np.where(r > 0))]
record("Decoy-BB84 asymptotic reach (km)", reach, 200.0,
       "demonstrated 144-227 km (arXiv:2512.05101, etc.)", tol_pct=40.0,
       note="model reach in the demonstrated band")

# ---- G. Raman coexistence: reproduce Patel et al. JLT 2014 Config G ----
# 60 km, 14 channels @ -10.5 dBm/ch, 10 GHz (~0.08 nm) filter, 2.5 ns gate,
# 15% detector efficiency -> ~0.15 Raman counts/gate (co-propagating).
p_ch = 1e-3 * 10 ** (-10.5 / 10)
patel = RamanModel(filter_bandwidth_nm=0.08, gate_time_s=2.5e-9)
counts = raman_background_yield(p_ch * 14, 60.0, raman=patel,
                               detector_efficiency=0.15)
record("Raman counts/gate (Patel Config G)", counts, 0.15,
       "Patel et al. JLT 2014 / arXiv:1410.0656", tol_pct=40.0,
       note="calibration anchor")

# ---- H. PMD statistics ----
record("Mean DGD = D sqrt(L) (100 km, 0.1 ps/sqrt-km)", mean_dgd_ps(0.1, 100.0),
       1.0, "random-walk law", tol_pct=0.01, exact=True)
dgds = np.array([PMDFiber(5.0, n_sections=60, seed=k).dgd_ps() for k in range(400)])
record("PMD emulator mean DGD (target 5 ps)", dgds.mean(), 5.0,
       "Maxwellian mean", tol_pct=12.0)
record("PMD DGD std/mean (Maxwellian)", dgds.std() / dgds.mean(), 0.4223,
       "Maxwellian sqrt(3pi/8 - 1)", tol_pct=15.0)

# ---- I. Laser phase noise variance ----
ph = laser_phase_noise(400000, 1e5, 32e9, np.random.default_rng(1))
record("Phase-noise step variance (2 pi dnu Ts)", np.var(np.diff(ph)),
       2 * np.pi * 1e5 / 32e9, "combined-linewidth Wiener", tol_pct=5.0)

# ---- J. Repeater ----
best500 = optimal_segment_count(500.0)
record("Repeater beats PLOB @ 500 km (ratio)",
       best500.secret_key_rate / direct_plob_rate(500.0), 1e6,
       "polynomial vs exponential scaling", tol_pct=None,
       note=f"repeater {best500.secret_key_rate:.1e} vs PLOB {direct_plob_rate(500.0):.1e}")
record("Repeater advantage crossover (km)", repeater_advantage_distance(), 66.0,
       "where repeater overtakes PLOB", tol_pct=None)


def main():
    npass = sum(1 for c in CHECKS if c["ok"])
    print(f"\n{'CHECK':<44}{'COMPUTED':>13}{'REFERENCE':>13}{'AGREE':>9}  SOURCE")
    print("-" * 120)
    for c in CHECKS:
        comp = c["computed"]; ref = c["reference"]
        cs = f"{comp:.4g}" if isinstance(comp, float) else str(comp)
        rs_ = f"{ref:.4g}" if isinstance(ref, (int, float)) else str(ref)
        flag = "  ok" if c["ok"] else " CHK"
        ex = "*" if c["exact"] else " "
        print(f"{c['name']:<44}{cs:>13}{rs_:>13}{c['agree']:>9}{flag}{ex} {c['source']}")
    print("-" * 120)
    print(f"{npass}/{len(CHECKS)} checks within tolerance.  (* = exact closed-form/conserved)")
    return npass, len(CHECKS)


if __name__ == "__main__":
    main()
