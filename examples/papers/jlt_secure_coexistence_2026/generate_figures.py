"""Regenerate every figure in the JLT secure-coexistence manuscript.

Run:  python generate_figures.py     (writes PNGs into ./figures/)

Requires the iQuant4 platform (iqcore, iq4comm). All physics comes from the
frozen configuration in config.py.
"""
import dataclasses
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from iqcore.fiber import SMF28, Amplifier
from iq4comm.qkd.coexistence import (
    classical_capacity_bps, coexistence_dv_key_rate, coexistence_cv_key_rate, RamanModel)
from iq4comm.qkd.cv import CVDetector
from iq4comm.qkd.multispan import multispan_dv_key_rate, multispan_classical_capacity_bps
from iq4comm.qkd.raman_spectrum import (
    band_raman_coefficient, spontaneous_raman_efficiency)
from iq4comm.dsp.gn_model import nli_coefficient, ase_power_w, optimal_launch_power_w
from config import CONFIG as C

OUT = "figures"
rho_c = band_raman_coefficient(C.quantum_cband_nm, C.classical_center_nm)
rho_o = band_raman_coefficient(C.quantum_oband_nm, C.classical_center_nm)
raman_c = RamanModel(raman_coeff_per_km_per_nm=rho_c, quantum_wavelength_nm=1550.0)
raman_o = RamanModel(raman_coeff_per_km_per_nm=rho_o, quantum_wavelength_nm=1310.0)
oband = dataclasses.replace(SMF28, attenuation_db_per_km=C.oband_attenuation_db_per_km)
det = CVDetector(efficiency=C.cv_efficiency, electronic_noise=C.cv_electronic_noise,
                 reconciliation_efficiency=C.cv_reconciliation)


def p_gn(L, nch, fiber=SMF28):
    amp = Amplifier(gain_db=fiber.loss_db(L), noise_figure_db=C.noise_figure_db)
    eta = nli_coefficient(fiber, L, 1, C.symbol_rate_baud, nch * C.spacing_hz)
    return 10 * np.log10(optimal_launch_power_w(ase_power_w(amp, 1, C.symbol_rate_baud), eta) / 1e-3)


def seclim(grid, a):
    ok = a >= C.r_min
    return grid[ok][-1] if ok.any() else np.nan


def fig_raman_profile():
    off = np.linspace(0.2, 40, 2000)
    st = np.array([spontaneous_raman_efficiency(f * 1e12) for f in off])
    an = np.array([spontaneous_raman_efficiency(-f * 1e12) for f in off])
    fig, ax = plt.subplots(figsize=(7, 4.4))
    ax.semilogy(off, st, color="#c0392b", lw=2.2, label="Stokes (classical above Q)")
    ax.semilogy(off, an, color="#1f3b8b", lw=2.2, ls="--", label="anti-Stokes (classical below Q)")
    ax.axvline(0.8, color="#149c7c", lw=1.4); ax.text(0.9, 3e-3, "in-band\nC-band", color="#149c7c", fontsize=9)
    ax.axvline(35.4, color="#8b5cf6", lw=1.4); ax.text(30.5, 3e-3, "O-band", color="#8b5cf6", fontsize=9, ha="right")
    ax.set_xlabel("classical-quantum offset |Δν| (THz)"); ax.set_ylabel(r"relative Raman efficiency $g_R\Phi$")
    ax.set_title("Wavelength-resolved spontaneous-Raman coexistence profile")
    ax.legend(fontsize=9, loc="lower center"); ax.set_ylim(1e-4, 20)
    fig.tight_layout(); fig.savefig(f"{OUT}/fig_raman_profile.png", dpi=160); plt.close(fig)


def fig_optimization():
    grid = np.linspace(-34, 4, 761)
    cap = np.array([classical_capacity_bps(p, C.n_channels, C.L_km, symbol_rate_baud=C.symbol_rate_baud,
                    channel_spacing_hz=C.spacing_hz, noise_figure_db=C.noise_figure_db) for p in grid]) / 1e12
    dvc = np.array([coexistence_dv_key_rate(C.L_km, p, C.n_channels, raman=raman_c) for p in grid])
    cvc = np.array([coexistence_cv_key_rate(C.L_km, p, C.n_channels, raman=raman_c, cv_detector=det) for p in grid])
    dvo = np.array([coexistence_dv_key_rate(C.L_km, p, C.n_channels, fiber=oband, raman=raman_o) for p in grid])
    PGN = p_gn(C.L_km, C.n_channels)
    fig, ax = plt.subplots(figsize=(7.2, 4.7)); ax2 = ax.twinx()
    ax.plot(grid, cap, color="#1f3b8b", lw=2.3, label="Classical rate")
    ax2.semilogy(grid, np.maximum(dvc, 1e-12), color="#c0392b", lw=2, label="DV-QKD, in-band C")
    ax2.semilogy(grid, np.maximum(cvc, 1e-12), color="#e67e22", lw=2, ls="-.", label="CV-QKD, in-band C")
    ax2.semilogy(grid, np.maximum(dvo, 1e-12), color="#149c7c", lw=2, ls="--", label="DV-QKD, O-band")
    ax2.axhline(C.r_min, color="grey", ls=":", lw=1.1)
    ax.axvline(PGN, color="#333", lw=1.6); ax.text(PGN - 0.4, 2.5, r"$P_{\rm GN}$", ha="right", fontsize=11)
    ax.set_xlabel("per-channel launch power (dBm)"); ax.set_ylabel("Classical rate (Tb/s)", color="#1f3b8b")
    ax2.set_ylabel("QKD secret-key rate"); ax2.set_ylim(1e-8, 1)
    ax.set_title("Quantum band and protocol set the coexistence headroom")
    l1, la1 = ax.get_legend_handles_labels(); l2, la2 = ax2.get_legend_handles_labels()
    ax.legend(l1 + l2, la1 + la2, fontsize=8.5, loc="lower left")
    fig.tight_layout(); fig.savefig(f"{OUT}/fig_optimization.png", dpi=160); plt.close(fig)


def fig_regime():
    dists = np.arange(10, 141, 5); grid = np.linspace(-30, 8, 761)
    PG = np.array([p_gn(L, C.n_channels) for L in dists])
    PS = np.array([seclim(grid, np.array([coexistence_dv_key_rate(L, p, C.n_channels, raman=raman_c) for p in grid])) for L in dists])
    fig, ax = plt.subplots(figsize=(7, 4.4))
    ax.plot(dists, PG, "-", color="#333", lw=2.2, label=r"$P_{\rm GN}$")
    ax.plot(dists, PS, "--", color="#c0392b", lw=2.2, label=r"$P^\star_{\rm sec}$ (DV)")
    cl = PS >= PG
    ax.fill_between(dists, -32, 9, where=cl, color="#149c7c", alpha=0.10)
    ax.fill_between(dists, -32, 9, where=~cl & ~np.isnan(PS), color="#c0392b", alpha=0.08)
    ax.set_xlabel("fiber length L (km)"); ax.set_ylabel("per-channel launch power (dBm)")
    ax.set_ylim(-32, 9); ax.set_xlim(10, 140); ax.set_title("Operating-regime partition (in-band C-band)")
    ax.legend(fontsize=9, loc="lower left")
    fig.tight_layout(); fig.savefig(f"{OUT}/fig_regime.png", dpi=160); plt.close(fig)


def fig_load():
    loads = [4, 8, 16, 24, 32, 40]; grid = np.linspace(-30, 6, 721)
    pg = [p_gn(C.L_km, n) for n in loads]
    ps = [seclim(grid, np.array([coexistence_dv_key_rate(C.L_km, p, n, raman=raman_c) for p in grid])) for n in loads]
    fig, ax = plt.subplots(figsize=(7, 4.2))
    ax.plot(loads, pg, "o-", color="#333", lw=2, label=r"$P_{\rm GN}$")
    ax.plot(loads, ps, "s--", color="#c0392b", lw=2, label=r"$P^\star_{\rm DV}$")
    ax.fill_between(loads, ps, pg, color="#c0392b", alpha=0.12)
    ax.set_xlabel("classical channels $N_c$"); ax.set_ylabel("per-channel launch power (dBm)")
    ax.set_title("Security headroom shrinks with loading"); ax.legend(fontsize=9)
    fig.tight_layout(); fig.savefig(f"{OUT}/fig_load.png", dpi=160); plt.close(fig)


def fig_multispan():
    spans = np.arange(1, 9)
    qkd = np.array([multispan_dv_key_rate(-2.0, C.n_channels, C.L_km, int(N), fiber=oband, raman=raman_o) for N in spans])
    cap = np.array([multispan_classical_capacity_bps(-2.0, C.n_channels, C.L_km, int(N)) for N in spans]) / 1e12
    fig, ax = plt.subplots(figsize=(7, 4.4)); ax2 = ax.twinx()
    ax.plot(spans * C.L_km, cap, "o-", color="#1f3b8b", lw=2, label="Classical (amplified)")
    ax2.semilogy(spans * C.L_km, np.maximum(qkd, 1e-12), "s--", color="#149c7c", lw=2, label="O-band QKD")
    ax2.axhline(C.r_min, color="grey", ls=":", lw=1.1)
    ax.set_xlabel("total link length (km)"); ax.set_ylabel("Classical rate (Tb/s)", color="#1f3b8b")
    ax2.set_ylabel("QKD secret-key rate", color="#149c7c"); ax2.set_ylim(1e-8, 1e-2)
    ax.set_title("Amplification asymmetry: classical survives, quantum cannot relay")
    l1, la1 = ax.get_legend_handles_labels(); l2, la2 = ax2.get_legend_handles_labels()
    ax.legend(l1 + l2, la1 + la2, fontsize=9, loc="upper right")
    fig.tight_layout(); fig.savefig(f"{OUT}/fig_multispan.png", dpi=160); plt.close(fig)


def fig_rmin():
    rmins = np.logspace(-8, -3, 26); grid = np.arange(-42, p_gn(C.L_km, C.n_channels) + 4, 0.02)
    dv = np.array([coexistence_dv_key_rate(C.L_km, p, C.n_channels, raman=raman_c) for p in grid])
    cv = np.array([coexistence_cv_key_rate(C.L_km, p, C.n_channels, raman=raman_c, cv_detector=det) for p in grid])
    PGN = p_gn(C.L_km, C.n_channels)
    bnd = lambda a, rm: (grid[a >= rm][-1] if (a >= rm).any() else np.nan)
    Pdv = [bnd(dv, rm) for rm in rmins]; Pcv = [bnd(cv, rm) for rm in rmins]
    fig, ax = plt.subplots(figsize=(7, 4.4))
    ax.semilogx(rmins, Pdv, "-", color="#c0392b", lw=2.2, label=r"$P^\star$, DV")
    ax.semilogx(rmins, Pcv, "--", color="#e67e22", lw=2.2, label=r"$P^\star$, CV")
    ax.axhline(PGN, color="#333", lw=1.4, ls=":")
    sec = ax.secondary_xaxis("top", functions=(lambda r: r * 1e9, lambda s: s / 1e9))
    sec.set_xlabel("secret-key rate at 1 GHz clock (bits/s)")
    ax.set_xlabel(r"security floor $R_{\min}$ (bits/use)"); ax.set_ylabel(r"secure launch $P^\star$ (dBm/ch)")
    ax.set_title("Operating point is insensitive to the security floor"); ax.legend(fontsize=9)
    fig.tight_layout(); fig.savefig(f"{OUT}/fig_rmin.png", dpi=160); plt.close(fig)


if __name__ == "__main__":
    import os
    os.makedirs(OUT, exist_ok=True)
    for fn in (fig_raman_profile, fig_optimization, fig_regime, fig_load, fig_multispan, fig_rmin):
        fn(); print(f"  wrote {fn.__name__}")
    print("all figures regenerated in ./figures/")
