"""QKD-classical coexistence over one DWDM fiber -- the iQuant4 integration.

Classical DWDM channels co-propagating with a quantum channel generate
**spontaneous Raman scattering (SpRS)** that leaks into the quantum band and
appears as extra detector background, degrading the QKD key rate.  This module
computes that coupling from the *same* :class:`iqcore.fiber.FiberSpec` that
drives the classical Gaussian-Noise performance, so a single physical fiber
description yields both the classical capacity and the secure key rate -- and
the tradeoff between them.

Coexistence is realistic but bounded: the Raman floor grows with classical
launch power, channel count, and effective length, so higher classical
throughput buys shorter quantum reach.  The headline output is the
capacity-vs-secret-key-rate operating curve and its secure/insecure boundary.

Raman background (forward-scattered, co-propagating approximation)::

    P_raman = P_classical_total * rho * B_filter * L_eff
    Y_raman = (P_raman / h nu_q) * t_gate * eta_det

where ``rho`` is the effective in-band Raman coefficient (per km per nm,
incorporating receiver filtering), ``B_filter`` the quantum filter bandwidth,
and ``t_gate`` the detector gate.  Defaults are representative; calibrate ``rho``
to measured system data.

References: Eraerds et al., NJP 12, 063027 (2010); coexistence reviews in JOCN.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from iqcore.fiber import Amplifier, FiberSpec, SMF28
from iq4comm.dsp.gn_model import nli_coefficient, ase_power_w, effective_snr
from .dv import DetectorModel, bb84_decoy_key_rate
from .cv import CVDetector, cvqkd_homodyne_key_rate

__all__ = [
    "RamanModel",
    "raman_background_yield",
    "raman_photon_occupation",
    "cv_raman_excess_noise",
    "coexistence_dv_key_rate",
    "coexistence_cv_key_rate",
    "classical_capacity_bps",
    "coexistence_curve",
    "CoexistencePoint",
]

_PLANCK_J_S = 6.62607015e-34
_C_M_PER_S = 2.99792458e8

# --- Measured spontaneous-Raman slopes for standard single-mode fiber --------
# Patel et al., "Impact of Raman Scattered Noise from Multiple Telecom Channels
# on Fiber-Optic QKD Systems," J. Lightwave Technol. 32(13), 2332 (2014);
# arXiv:1410.0656, Table II.  Slopes are the Raman count-probability per gate
# per km of fiber per 100 GHz of quantum-classical spectral separation, measured
# at a 10 GHz detection bandwidth and 2.5 ns gate (co-propagating / forward).
# Anti-Stokes (quantum below the classical pump) is ~1.6x noisier than Stokes.
MEASURED_RAMAN_SLOPE_STOKES_FWD = 6.9e-12       # per km per 100 GHz, ref 10 GHz / 2.5 ns
MEASURED_RAMAN_SLOPE_ANTISTOKES_FWD = 11.5e-12
MEASURED_RAMAN_REF_BANDWIDTH_GHZ = 10.0
MEASURED_RAMAN_REF_GATE_NS = 2.5


@dataclass(frozen=True)
class RamanModel:
    """Spontaneous-Raman coexistence-noise parameters.

    The default coefficient is **calibrated to measured data**: it reproduces the
    Configuration-G operating point of Patel et al. (JLT 2014 / arXiv:1410.0656)
    -- 14 classical channels at -10.5 dBm/channel over 60 km with a 10 GHz filter
    and 2.5 ns gate at 15% detector efficiency, giving ~0.15 Raman counts per gate
    (co-propagating).  Solving the count-probability model at those conditions
    yields ``rho ~ 2.5e-8 /(km*nm)`` (about 5x higher than an earlier
    representative guess of 5e-9 -- i.e. the Raman floor is *stronger*, and
    coexistence *less* forgiving, than an uncalibrated estimate suggests).

    The anchor value (~0.15 counts/gate) comes from a reported figure and carries
    a factor-of-a-few uncertainty; the offset dependence is folded into the
    effective coefficient.  Recalibrate ``raman_coeff_per_km_per_nm`` to your own
    measured background or hardware for publication-grade numbers.  See
    ``MEASURED_RAMAN_SLOPE_*`` for the underlying measured slopes.

    Attributes
    ----------
    raman_coeff_per_km_per_nm:
        Effective in-band Raman scattering coefficient ``rho`` (1/(km*nm)).
    filter_bandwidth_nm:
        Quantum-channel optical filter bandwidth (nm).
    gate_time_s:
        Detector gate duration (s).
    quantum_wavelength_nm:
        Quantum-channel wavelength (sets the photon energy).
    """

    # Calibrated to Patel et al. JLT 2014 Config G (~0.15 counts/gate); see above.
    raman_coeff_per_km_per_nm: float = 2.5e-8
    filter_bandwidth_nm: float = 0.01
    gate_time_s: float = 1e-10
    quantum_wavelength_nm: float = 1550.0


def raman_background_yield(classical_total_power_w: float, distance_km: float, *,
                           fiber: FiberSpec = SMF28,
                           raman: RamanModel | None = None,
                           detector_efficiency: float = 0.5) -> float:
    """Detector background yield (per gate) from co-propagating classical power."""
    raman = raman or RamanModel()
    l_eff = fiber.effective_length_km(distance_km)
    p_raman = (classical_total_power_w * raman.raman_coeff_per_km_per_nm
               * raman.filter_bandwidth_nm * l_eff)
    nu = _C_M_PER_S / (raman.quantum_wavelength_nm * 1e-9)
    photon_energy = _PLANCK_J_S * nu
    photons_per_gate = p_raman / photon_energy * raman.gate_time_s
    return photons_per_gate * detector_efficiency


def raman_photon_occupation(classical_total_power_w: float, distance_km: float, *,
                            fiber: FiberSpec = SMF28,
                            raman: RamanModel | None = None) -> float:
    """Mean Raman noise-photon occupation per optical mode ``n_bar``.

    Filter-independent single-mode occupation; the DV background integrates many
    such modes (``n_bar * B_filter * t_gate``) while a CV homodyne receiver sees
    exactly one mode.  This is the shared quantity that links the two protocols'
    coexistence penalties.
    """
    raman = raman or RamanModel()
    l_eff = fiber.effective_length_km(distance_km)
    p_raman = (classical_total_power_w * raman.raman_coeff_per_km_per_nm
               * raman.filter_bandwidth_nm * l_eff)
    lam_m = raman.quantum_wavelength_nm * 1e-9
    photon_energy = _PLANCK_J_S * (_C_M_PER_S / lam_m)
    filter_bandwidth_hz = (_C_M_PER_S / lam_m ** 2) * (raman.filter_bandwidth_nm * 1e-9)
    return p_raman / (photon_energy * filter_bandwidth_hz)


def cv_raman_excess_noise(classical_total_power_w: float, distance_km: float, *,
                          fiber: FiberSpec = SMF28,
                          raman: RamanModel | None = None) -> float:
    """CV-QKD excess noise (SNU) from co-propagating classical power.

    A thermal Raman background of occupation ``n_bar`` adds ``2 * n_bar`` to the
    quadrature variance (both quadratures) referred to the receiver.
    """
    n_bar = raman_photon_occupation(classical_total_power_w, distance_km,
                                    fiber=fiber, raman=raman)
    return 2.0 * n_bar


def coexistence_cv_key_rate(distance_km: float, launch_power_dbm_per_channel: float,
                            n_channels: int, *, fiber: FiberSpec = SMF28,
                            cv_detector: CVDetector | None = None,
                            raman: RamanModel | None = None,
                            modulation_variance: float = 4.0,
                            intrinsic_excess_noise: float = 0.01,
                            finite: "FiniteKeyParams | None" = None) -> float:
    """CV-QKD (GG02 homodyne) key rate with classical DWDM channels present."""
    p_ch_w = 1e-3 * 10.0 ** (launch_power_dbm_per_channel / 10.0)
    p_total = p_ch_w * n_channels
    xi_raman = cv_raman_excess_noise(p_total, distance_km, fiber=fiber, raman=raman)
    t = fiber.transmissivity(distance_km)
    return cvqkd_homodyne_key_rate(
        t, modulation_variance=modulation_variance,
        excess_noise=intrinsic_excess_noise + xi_raman, detector=cv_detector,
        finite=finite)


def coexistence_dv_key_rate(distance_km: float, launch_power_dbm_per_channel: float,
                            n_channels: int, *, fiber: FiberSpec = SMF28,
                            detector: DetectorModel | None = None,
                            raman: RamanModel | None = None,
                            mu: float = 0.5) -> float:
    """DV-QKD secret-key rate with classical DWDM channels co-propagating."""
    detector = detector or DetectorModel()
    p_ch_w = 1e-3 * 10.0 ** (launch_power_dbm_per_channel / 10.0)
    p_total = p_ch_w * n_channels
    bg = raman_background_yield(p_total, distance_km, fiber=fiber, raman=raman,
                                detector_efficiency=detector.efficiency)
    eta = fiber.transmissivity(distance_km)
    return bb84_decoy_key_rate(eta, mu, detector=detector, background_yield=bg)


def classical_capacity_bps(launch_power_dbm_per_channel: float, n_channels: int,
                           distance_km: float, *, fiber: FiberSpec = SMF28,
                           symbol_rate_baud: float = 32e9,
                           channel_spacing_hz: float = 50e9,
                           noise_figure_db: float = 5.0) -> float:
    """Aggregate classical Shannon capacity (bits/s) over one span, GN-limited.

    Single amplifier-free span (as in QKD coexistence): ASE from one preamp,
    NLI from one span; capacity = n_ch * R_s * log2(1 + SNR_eff).
    """
    amp = Amplifier(gain_db=fiber.loss_db(distance_km), noise_figure_db=noise_figure_db)
    wdm_bw = n_channels * channel_spacing_hz
    eta_nli = nli_coefficient(fiber, distance_km, 1, symbol_rate_baud, wdm_bw)
    p_ase = ase_power_w(amp, 1, symbol_rate_baud)
    p_ch_w = 1e-3 * 10.0 ** (launch_power_dbm_per_channel / 10.0)
    snr = effective_snr(p_ch_w, p_ase, eta_nli)
    return n_channels * symbol_rate_baud * np.log2(1.0 + snr)


@dataclass(frozen=True)
class CoexistencePoint:
    launch_dbm: float
    classical_capacity_bps: float
    secret_key_rate: float
    secure: bool


def coexistence_curve(distance_km: float, n_channels: int,
                      launch_dbm_grid, *, fiber: FiberSpec = SMF28,
                      detector: DetectorModel | None = None,
                      raman: RamanModel | None = None,
                      symbol_rate_baud: float = 32e9,
                      channel_spacing_hz: float = 50e9,
                      mu: float = 0.5) -> list[CoexistencePoint]:
    """Classical capacity and QKD key rate versus classical launch power."""
    out = []
    for pdbm in launch_dbm_grid:
        cap = classical_capacity_bps(pdbm, n_channels, distance_km, fiber=fiber,
                                     symbol_rate_baud=symbol_rate_baud,
                                     channel_spacing_hz=channel_spacing_hz)
        skr = coexistence_dv_key_rate(distance_km, pdbm, n_channels, fiber=fiber,
                                      detector=detector, raman=raman, mu=mu)
        out.append(CoexistencePoint(float(pdbm), cap, skr, skr > 0.0))
    return out
