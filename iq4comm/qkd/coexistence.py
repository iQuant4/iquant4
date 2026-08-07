"""QKD-classical coexistence over one DWDM fiber -- the iQuant4 integration.

Classical DWDM channels co-propagating with a quantum channel generate
**spontaneous Raman scattering (SpRS)** that leaks into the quantum band and
appears as extra detector background, degrading the QKD key rate.  This module
computes that coupling from the *same* :class:`iqcore.fiber.FiberSpec` that
drives the classical Gaussian-Noise performance, so a single physical fiber
description yields both the classical capacity and the secure key rate -- and
the tradeoff between them.

Coexistence is realistic but bounded: the Raman floor grows with classical
launch power, channel count, and the direction-dependent longitudinal path
integral, so higher classical throughput buys shorter quantum reach.  The headline output is the
capacity-vs-secret-key-rate operating curve and its secure/insecure boundary.

Raman background is obtained from the longitudinal scattering integral.  For
co-propagation, with launched pump power ``P_p(0)`` and the quantum receiver at
``z=L``::

    P_raman = P_p(0) * rho * B_filter
              * integral_0^L exp(-alpha_p*z) exp(-alpha_q*(L-z)) dz

For counter-propagation the classical transmitter is beside the quantum
receiver, so both the pump and the back-scattered Raman photon traverse
``L-z`` before the photon is collected::

    P_raman = P_p(L) * rho * B_filter
              * integral_0^L exp(-(alpha_p+alpha_q)*(L-z)) dz

In both cases::

    Y_raman = (P_raman / h nu_q) * t_gate * eta_det

where ``rho`` is the effective in-band Raman coefficient (per km per nm,
incorporating receiver filtering), ``B_filter`` the quantum filter bandwidth,
and ``t_gate`` the detector gate.  ``alpha_p`` and ``alpha_q`` are power-loss
coefficients in nepers/km at the classical-pump and quantum wavelengths.
Defaults are representative; calibrate ``rho`` to measured system data.

References: Eraerds et al., NJP 12, 063027 (2010); coexistence reviews in JOCN.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

import numpy as np

from iqcore.fiber import Amplifier, FiberSpec, SMF28
from iq4comm.dsp.gn_model import nli_coefficient, ase_power_w, effective_snr
from .dv import DetectorModel, bb84_decoy_key_rate
from .cv import CVDetector, cvqkd_homodyne_key_rate
from .raman_spectrum import ANCHOR_RHO_PER_KM_PER_NM

__all__ = [
    "RamanDirection",
    "RamanModel",
    "raman_path_integral_km",
    "raman_received_power_w",
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
_DB_TO_NEPER = np.log(10.0) / 10.0

RamanDirection = Literal["co", "counter"]

# --- Measured spontaneous-Raman slopes for standard single-mode fiber --------
# da Silva et al., "Impact of Raman Scattered Noise from Multiple Telecom Channels
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

    The default coefficient is **calibrated to measured data**: a locked
    digitisation of the six co-propagating Configuration-G points in Fig. 4(a)
    of Ferreira da Silva et al. (JLT 2014 / arXiv:1410.0656).  The experiment
    used 14 classical channels at -10.5 dBm/channel, a 10 GHz filter, a 2.5 ns
    gate, and 15% detector efficiency.  A shape/scale fit gives
    ``alpha = 0.300 dB/km`` and ``rho = 4.708e-10 /(km*nm)``; the extra measured
    link losses explain why this attenuation is above nominal SMF-28.

    Figure 4 reports probabilities on a ``x10^-4`` axis.  An earlier iQuant4
    calibration mistakenly treated the 60 km value as approximately ``0.15``
    counts/gate; the digitised value is approximately ``1.2e-4``.  The default
    is an *effective receiver-side coefficient* containing the paper's
    filtering/collection conventions, not a universal silica constant.
    Recalibrate it to your own receiver for publication-grade absolute rates.

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
    propagation_direction:
        ``"co"`` when classical and quantum signals share a launch end, or
        ``"counter"`` when the classical transmitter is beside the quantum
        receiver.  The supplied classical power is always the power at the
        classical transmitter for the selected direction.
    pump_attenuation_db_per_km:
        Classical-pump power attenuation in dB/km.  ``None`` uses the quantum
        path's :class:`~iqcore.fiber.FiberSpec` attenuation, which is suitable
        for an in-band system.  Set this explicitly for mixed-band coexistence,
        e.g. a 1550 nm pump with a 1310 nm quantum channel.
    """

    # Effective co-propagating Config-G fit; see the class documentation above.
    raman_coeff_per_km_per_nm: float = ANCHOR_RHO_PER_KM_PER_NM
    filter_bandwidth_nm: float = 0.01
    gate_time_s: float = 1e-10
    quantum_wavelength_nm: float = 1550.0
    propagation_direction: RamanDirection = "co"
    pump_attenuation_db_per_km: float | None = None

    def __post_init__(self) -> None:
        if self.propagation_direction not in ("co", "counter"):
            raise ValueError("propagation_direction must be 'co' or 'counter'")
        if (self.pump_attenuation_db_per_km is not None
                and self.pump_attenuation_db_per_km < 0.0):
            raise ValueError("pump_attenuation_db_per_km must be non-negative")


def raman_path_integral_km(distance_km: float, *,
                           pump_attenuation_db_per_km: float,
                           quantum_attenuation_db_per_km: float,
                           propagation_direction: RamanDirection = "co") -> float:
    """Longitudinal Raman collection integral in kilometres.

    Parameters use power attenuation in dB/km and are converted once to
    nepers/km.  The returned value is the path factor that multiplies launched
    pump power, the local Raman coefficient, and receiver bandwidth.

    For co-propagation the closed form is

    ``(exp(-alpha_q*L) - exp(-alpha_p*L)) / (alpha_p - alpha_q)``,

    with the equal-loss limit ``L*exp(-alpha*L)``.  For counter-propagation it is

    ``(1 - exp(-(alpha_p+alpha_q)*L)) / (alpha_p+alpha_q)``.

    The supplied pump power is defined at its own transmitter: ``z=0`` for
    ``"co"`` and ``z=L`` for ``"counter"``.  ``numpy.expm1`` is used at the
    removable singularities to keep the result accurate for small loss.
    """
    if distance_km < 0.0:
        raise ValueError("distance_km must be non-negative")
    if pump_attenuation_db_per_km < 0.0:
        raise ValueError("pump_attenuation_db_per_km must be non-negative")
    if quantum_attenuation_db_per_km < 0.0:
        raise ValueError("quantum_attenuation_db_per_km must be non-negative")
    if propagation_direction not in ("co", "counter"):
        raise ValueError("propagation_direction must be 'co' or 'counter'")
    if distance_km == 0.0:
        return 0.0

    alpha_p = pump_attenuation_db_per_km * _DB_TO_NEPER
    alpha_q = quantum_attenuation_db_per_km * _DB_TO_NEPER
    length = float(distance_km)

    if propagation_direction == "counter":
        alpha_sum = alpha_p + alpha_q
        if alpha_sum == 0.0:
            return length
        return float(-np.expm1(-alpha_sum * length) / alpha_sum)

    alpha_delta = alpha_p - alpha_q
    scaled_delta = alpha_delta * length
    if alpha_delta == 0.0:
        return float(length * np.exp(-alpha_q * length))
    if abs(scaled_delta) < 1e-6:
        return float(
            np.exp(-alpha_q * length)
            * (-np.expm1(-scaled_delta) / alpha_delta)
        )
    return float(
        (np.exp(-alpha_q * length) - np.exp(-alpha_p * length))
        / alpha_delta
    )


def _raman_path_integral_from_model(distance_km: float, fiber: FiberSpec,
                                    raman: RamanModel) -> float:
    pump_loss = raman.pump_attenuation_db_per_km
    if pump_loss is None:
        pump_loss = fiber.attenuation_db_per_km
    return raman_path_integral_km(
        distance_km,
        pump_attenuation_db_per_km=pump_loss,
        quantum_attenuation_db_per_km=fiber.attenuation_db_per_km,
        propagation_direction=raman.propagation_direction,
    )


def raman_received_power_w(classical_total_power_w: float, distance_km: float, *,
                           fiber: FiberSpec = SMF28,
                           raman: RamanModel | None = None) -> float:
    """Receiver-side spontaneous-Raman power in the quantum filter band.

    ``classical_total_power_w`` is the total classical power at the classical
    transmitter for the direction declared by ``raman``.  ``fiber`` describes
    the quantum path, including its wavelength-specific attenuation; the pump
    attenuation is taken from ``raman.pump_attenuation_db_per_km`` or falls back
    to the same fiber loss for in-band operation.
    """
    raman = raman or RamanModel()
    path_integral = _raman_path_integral_from_model(distance_km, fiber, raman)
    return float(
        classical_total_power_w
        * raman.raman_coeff_per_km_per_nm
        * raman.filter_bandwidth_nm
        * path_integral
    )


def raman_background_yield(classical_total_power_w: float, distance_km: float, *,
                           fiber: FiberSpec = SMF28,
                           raman: RamanModel | None = None,
                           detector_efficiency: float = 0.5) -> float:
    """Detector background yield (per gate) from classical coexistence power."""
    raman = raman or RamanModel()
    p_raman = raman_received_power_w(classical_total_power_w, distance_km,
                                     fiber=fiber, raman=raman)
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
    p_raman = raman_received_power_w(classical_total_power_w, distance_km,
                                     fiber=fiber, raman=raman)
    lam_m = raman.quantum_wavelength_nm * 1e-9
    photon_energy = _PLANCK_J_S * (_C_M_PER_S / lam_m)
    filter_bandwidth_hz = (_C_M_PER_S / lam_m ** 2) * (raman.filter_bandwidth_nm * 1e-9)
    return p_raman / (photon_energy * filter_bandwidth_hz)


def cv_raman_excess_noise(classical_total_power_w: float, distance_km: float, *,
                          fiber: FiberSpec = SMF28,
                          raman: RamanModel | None = None) -> float:
    """Input-referred CV-QKD excess noise (SNU) from classical coexistence power.

    ``raman_photon_occupation`` returns the *two-polarization* Raman occupation
    ``n_bar`` of the detected temporal-spectral mode.  A homodyne local
    oscillator selects a single polarization, so the CV mode sees ``n_bar / 2``;
    both quadratures then pick up a receiver-referred excess noise
    ``xi_rx = 2 * (n_bar / 2) = n_bar``.  The GG02 Holevo bound is evaluated with
    the noise referred to the *channel input*, which divides by the quantum
    transmissivity ``T_q`` (equivalently, the manuscript's
    ``xi_R = 2 * n_bar_pol / T_q``)::

        xi_R = n_bar / T_q .

    This is the single, consistent normalization shared with the DV background
    ``mu_R = P_R * tau_g / (h nu)`` through ``mu_R = 2 * B_q * tau_g * n_bar_pol``.
    """
    n_bar = raman_photon_occupation(classical_total_power_w, distance_km,
                                    fiber=fiber, raman=raman)
    t = fiber.transmissivity(distance_km)
    if t <= 0.0:
        return float("inf")
    return n_bar / t


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
