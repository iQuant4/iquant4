"""Audit the common Raman-to-DV/CV normalization used in the JLT paper.

The script uses the reported DV security boundary to infer the Raman photons
per gate.  It then maps the same total, unpolarized Raman PSD into the
LO-selected CV mode and recomputes the trusted-detector RR-GMCS boundary.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from scipy.optimize import brentq


@dataclass(frozen=True)
class Config:
    wavelength_m: float = 1546.12e-9
    filter_width_nm: float = 0.01
    gate_s: float = 0.1e-9
    length_km: float = 80.0
    attenuation_db_per_km: float = 0.2
    r_min: float = 1e-6
    psec_dv_dbm: float = -13.2

    mu_signal: float = 0.5
    eta_d: float = 0.5
    e_d: float = 0.02
    p_dark: float = 1e-6
    f_ec: float = 1.16
    q_sift: float = 0.5

    v_a: float = 4.0
    eta_h: float = 0.6
    v_el: float = 0.05
    xi_int: float = 0.01
    beta: float = 0.95

    ase_plus_imp_w: float = 2.6e-7
    eta_gn_per_w2: float = 9.8e2


def binary_entropy(x: float) -> float:
    if x <= 0.0 or x >= 1.0:
        return 0.0
    return -x * math.log2(x) - (1.0 - x) * math.log2(1.0 - x)


def bosonic_entropy(x: float) -> float:
    if x <= 1e-15:
        return 0.0
    return (x + 1.0) * math.log2(x + 1.0) - x * math.log2(x)


def dv_rate(mu_r: float, cfg: Config, transmissivity: float) -> float:
    y0 = 1.0 - (1.0 - cfg.p_dark) ** 2 * math.exp(-cfg.eta_d * mu_r)
    eta_sys = transmissivity * cfg.eta_d
    q_mu = 1.0 - (1.0 - y0) * math.exp(-eta_sys * cfg.mu_signal)
    e_mu = (
        0.5 * y0
        + cfg.e_d * (1.0 - math.exp(-eta_sys * cfg.mu_signal))
    ) / q_mu
    y1 = 1.0 - (1.0 - y0) * (1.0 - eta_sys)
    q1 = cfg.mu_signal * math.exp(-cfg.mu_signal) * y1
    e1 = (0.5 * y0 + cfg.e_d * eta_sys) / y1
    raw = cfg.q_sift * (
        q1 * (1.0 - binary_entropy(e1))
        - cfg.f_ec * q_mu * binary_entropy(e_mu)
    )
    return max(0.0, raw)


def cv_rate(xi_r: float, cfg: Config, transmissivity: float) -> float:
    """Standard trusted-homodyne RR-GMCS rate in vacuum-variance-one SNU."""
    v = cfg.v_a + 1.0
    chi_line = (1.0 - transmissivity) / transmissivity + cfg.xi_int + xi_r
    chi_hom = (1.0 - cfg.eta_h + cfg.v_el) / cfg.eta_h
    chi_tot = chi_line + chi_hom / transmissivity
    i_ab = 0.5 * math.log2((v + chi_tot) / (1.0 + chi_tot))

    a = (
        v * v * (1.0 - 2.0 * transmissivity)
        + 2.0 * transmissivity
        + transmissivity**2 * (v + chi_line) ** 2
    )
    b = transmissivity**2 * (v * chi_line + 1.0) ** 2
    root_ab = math.sqrt(max(0.0, a * a - 4.0 * b))
    lam1 = math.sqrt(max(1.0, (a + root_ab) / 2.0))
    lam2 = math.sqrt(max(1.0, (a - root_ab) / 2.0))

    c = (
        a * chi_hom
        + v * math.sqrt(b)
        + transmissivity * (v + chi_line)
    ) / (transmissivity * (v + chi_tot))
    d = (
        math.sqrt(b) * (v + math.sqrt(b) * chi_hom)
        / (transmissivity * (v + chi_tot))
    )
    root_cd = math.sqrt(max(0.0, c * c - 4.0 * d))
    lam3 = math.sqrt(max(1.0, (c + root_cd) / 2.0))
    lam4 = math.sqrt(max(1.0, (c - root_cd) / 2.0))
    chi_be = (
        bosonic_entropy((lam1 - 1.0) / 2.0)
        + bosonic_entropy((lam2 - 1.0) / 2.0)
        - bosonic_entropy((lam3 - 1.0) / 2.0)
        - bosonic_entropy((lam4 - 1.0) / 2.0)
    )
    return max(0.0, cfg.beta * i_ab - chi_be)


def classical_rate_factor(power_w: float, cfg: Config) -> float:
    snr = power_w / (
        cfg.ase_plus_imp_w + cfg.eta_gn_per_w2 * power_w**3
    )
    return math.log2(1.0 + snr)


def main() -> None:
    cfg = Config()
    trans = 10.0 ** (
        -cfg.attenuation_db_per_km * cfg.length_km / 10.0
    )
    b_q = (
        299_792_458.0
        / cfg.wavelength_m**2
        * cfg.filter_width_nm
        * 1e-9
    )

    mu_r_dv = brentq(
        lambda value: dv_rate(value, cfg, trans) - cfg.r_min,
        0.0,
        1.0,
    )
    y_r = 1.0 - math.exp(-cfg.eta_d * mu_r_dv)

    # P_R/(h nu B_q) = mu_R/(B_q tau_g).  For total unpolarized
    # Raman power, this equals the receiver-side quadrature excess noise:
    # one half of the PSD is LO-polarization matched and xi_rx=2*n_matched.
    xi_r_input_at_dv_boundary = mu_r_dv / (b_q * cfg.gate_s * trans)

    def cv_rate_at_launch_dbm(power_dbm: float) -> float:
        scale = 10.0 ** ((power_dbm - cfg.psec_dv_dbm) / 10.0)
        return cv_rate(xi_r_input_at_dv_boundary * scale, cfg, trans)

    psec_cv_dbm = brentq(
        lambda value: cv_rate_at_launch_dbm(value) - cfg.r_min,
        -40.0,
        0.0,
    )

    p_gn_w = (
        cfg.ase_plus_imp_w / (2.0 * cfg.eta_gn_per_w2)
    ) ** (1.0 / 3.0)
    p_gn_dbm = 10.0 * math.log10(p_gn_w / 1e-3)
    r_gn = classical_rate_factor(p_gn_w, cfg)

    def penalty(power_dbm: float) -> float:
        power_w = 1e-3 * 10.0 ** (power_dbm / 10.0)
        return 1.0 - classical_rate_factor(power_w, cfg) / r_gn

    print(f"T_q                         = {trans:.12g}")
    print(f"B_q                         = {b_q/1e9:.9f} GHz")
    print(f"B_q tau_g                   = {b_q*cfg.gate_s:.9f}")
    print(f"mu_R at DV boundary         = {mu_r_dv:.12g}")
    print(f"Y_R at DV boundary          = {y_r:.12g}")
    print(f"xi_R,input at DV boundary   = {xi_r_input_at_dv_boundary:.12g}")
    print(f"P_GN                        = {p_gn_dbm:.6f} dBm/ch")
    print()
    print("Protocol             P_sec [dBm/ch]   Back-off [dB]   Penalty")
    print(
        f"DV BB84              {cfg.psec_dv_dbm:12.6f}"
        f"   {p_gn_dbm-cfg.psec_dv_dbm:13.6f}   "
        f"{penalty(cfg.psec_dv_dbm):.9f}"
    )
    print(
        f"CV GMCS corrected    {psec_cv_dbm:12.6f}"
        f"   {p_gn_dbm-psec_cv_dbm:13.6f}   "
        f"{penalty(psec_cv_dbm):.9f}"
    )

    # Diagnostic: the old equation xi_R=2P_R/(h nu B_m T_q) reproduces
    # the reported -8.6 dBm boundary only when B_m is about 49.2 GHz.
    xi_required = xi_r_input_at_dv_boundary * 10.0 ** (
        (psec_cv_dbm - cfg.psec_dv_dbm) / 10.0
    )
    old_reported_cv_dbm = -8.6
    old_scale = 10.0 ** (
        (old_reported_cv_dbm - cfg.psec_dv_dbm) / 10.0
    )
    inferred_old_bm = (
        2.0 * mu_r_dv * old_scale
        / (cfg.gate_s * trans * xi_required)
    )
    correction = inferred_old_bm / (2.0 * b_q)
    print()
    print(f"Inferred old B_m            = {inferred_old_bm/1e9:.6f} GHz")
    print(f"CV-noise correction factor  = {correction:.6f}")
    print(f"CV-noise correction         = {10*math.log10(correction):.6f} dB")


if __name__ == "__main__":
    main()
