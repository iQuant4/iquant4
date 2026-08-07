"""One-command reproduction of the JLT secure-coexistence paper.

    python run_all.py

Prints the headline numbers table and regenerates all figures.  The security
ceiling and the classical GN optimum are reported separately so that a
non-binding security constraint cannot be mistaken for launch-power back-off.
"""
import numpy as np
from iqcore.fiber import SMF28, Amplifier
from iq4comm.qkd.coexistence import (classical_capacity_bps, coexistence_dv_key_rate,
                                     coexistence_cv_key_rate, RamanModel)
from iq4comm.qkd.cv import CVDetector
from iq4comm.qkd.raman_spectrum import band_raman_coefficient
from iq4comm.dsp.gn_model import nli_coefficient, ase_power_w, optimal_launch_power_w
from config import CONFIG as C


def headline():
    rho_c = band_raman_coefficient(C.quantum_cband_nm, C.classical_center_nm)
    rho_o = band_raman_coefficient(C.quantum_oband_nm, C.classical_center_nm)
    raman_c = RamanModel(raman_coeff_per_km_per_nm=rho_c, quantum_wavelength_nm=1550.0)
    det = CVDetector(efficiency=C.cv_efficiency, electronic_noise=C.cv_electronic_noise,
                     reconciliation_efficiency=C.cv_reconciliation)
    amp = Amplifier(gain_db=SMF28.loss_db(C.L_km), noise_figure_db=C.noise_figure_db)
    eta = nli_coefficient(SMF28, C.L_km, 1, C.symbol_rate_baud, C.n_channels * C.spacing_hz)
    A = ase_power_w(amp, 1, C.symbol_rate_baud)
    PGN = 10 * np.log10(optimal_launch_power_w(A, eta) / 1e-3)
    grid = np.linspace(-40, 16, 1121)
    rcl = lambda p: classical_capacity_bps(p, C.n_channels, C.L_km, symbol_rate_baud=C.symbol_rate_baud,
                                           channel_spacing_hz=C.spacing_hz, noise_figure_db=C.noise_figure_db) / 1e12
    r0 = rcl(PGN)
    sl = lambda a: (grid[a >= C.r_min][-1] if (a >= C.r_min).any() else np.nan)
    Pdv_sec = sl(np.array([coexistence_dv_key_rate(C.L_km, p, C.n_channels, raman=raman_c) for p in grid]))
    Pcv_sec = sl(np.array([coexistence_cv_key_rate(C.L_km, p, C.n_channels, raman=raman_c, cv_detector=det) for p in grid]))
    Pdv = min(PGN, Pdv_sec) if np.isfinite(Pdv_sec) else np.nan
    Pcv = min(PGN, Pcv_sec) if np.isfinite(Pcv_sec) else np.nan
    print("=== Headline numbers (Table III) ===")
    print(f"  eta_GN = {eta:.1f} /W^2   A = {A:.2e} W")
    print(f"  P_GN          = {PGN:6.2f} dBm/ch   R_cl0 = {r0:.2f} Tb/s")
    print(f"  DV  P_sec,max = {Pdv_sec:6.2f} dBm/ch   P* = {Pdv:6.2f}   back-off {PGN-Pdv:5.2f} dB   penalty {100*(1-rcl(Pdv)/r0):.1f}%")
    print(f"  CV  P_sec,max = {Pcv_sec:6.2f} dBm/ch   P* = {Pcv:6.2f}   back-off {PGN-Pcv:5.2f} dB   penalty {100*(1-rcl(Pcv)/r0):.1f}%")
    print(f"  O-band Raman  = {10*np.log10(rho_c/rho_o):.1f} dB quieter")


if __name__ == "__main__":
    headline()
    print()
    import generate_figures  # regenerates on import? no -- call main
    for fn in (generate_figures.fig_raman_profile, generate_figures.fig_optimization,
               generate_figures.fig_regime, generate_figures.fig_load,
               generate_figures.fig_multispan, generate_figures.fig_rmin):
        fn()
    print("figures regenerated in ./figures/")
    print("\nRun the validations separately:")
    print("  python fock_chi_be.py         # Table IV: chi_N(B:E) vs symplectic")
    print("  python fock_validation.py     # Table III entropy primitives")
    print("  python raman_dv_cv_audit.py   # DV/CV normalization audit")
