"""Multi-span coexistence: classical amplification vs. an un-amplified quantum channel.

A long classical link is built from ``N`` fibre spans with an inline EDFA after
each span restoring the per-channel power to the launch level.  The **classical**
channels therefore see per-span noise accumulation (ASE + NLI grow with span
count) but keep a workable SNR.

The **quantum** channel cannot be amplified: an inline EDFA would destroy the
quantum state (and, for an in-band C-band quantum channel, an EDFA would in any
case swamp it).  The physically consistent multi-span coexistence scenario is
therefore an **O-band quantum channel** riding a **C-band amplified** classical
link: the quantum photons traverse the *full, un-amplified* end-to-end loss,
while every span injects fresh spontaneous-Raman noise into the quantum band.

Two consequences, both captured here:

* Quantum-signal transmissivity falls as ``eta_span ** N`` (full end-to-end loss).
* Raman noise generated in span ``k`` still has to cross the remaining ``N-k``
  un-amplified spans to reach the receiver, so the accumulated background is
  ``sum_{k=1..N} eta_span ** (N-k)`` times a single span's generation.  This sum
  saturates while the signal keeps shrinking -- so the Raman-to-signal ratio
  grows sharply with span count, which is what limits QKD reach on amplified
  links.

The classical side reuses the validated GN + ASE model with ``n_spans``.
"""

from __future__ import annotations

import numpy as np

from iqcore.fiber import Amplifier, FiberSpec, SMF28
from iq4comm.dsp.gn_model import nli_coefficient, ase_power_w, effective_snr
from .coexistence import RamanModel, _PLANCK_J_S, _C_M_PER_S
from .dv import DetectorModel, bb84_decoy_key_rate
from .cv import CVDetector, cvqkd_homodyne_key_rate

__all__ = [
    "multispan_classical_capacity_bps",
    "multispan_raman_background_yield",
    "multispan_raman_photon_occupation",
    "multispan_dv_key_rate",
    "multispan_cv_key_rate",
]


def multispan_classical_capacity_bps(launch_dbm_per_channel: float, n_channels: int,
                                     span_length_km: float, n_spans: int, *,
                                     fiber: FiberSpec = SMF28,
                                     symbol_rate_baud: float = 32e9,
                                     channel_spacing_hz: float = 50e9,
                                     noise_figure_db: float = 5.0) -> float:
    """Aggregate classical Shannon capacity over ``n_spans`` amplified spans."""
    amp = Amplifier(gain_db=fiber.loss_db(span_length_km), noise_figure_db=noise_figure_db)
    wdm_bw = n_channels * channel_spacing_hz
    eta_nli = nli_coefficient(fiber, span_length_km, n_spans, symbol_rate_baud, wdm_bw)
    p_ase = ase_power_w(amp, n_spans, symbol_rate_baud)
    p_ch_w = 1e-3 * 10.0 ** (launch_dbm_per_channel / 10.0)
    snr = effective_snr(p_ch_w, p_ase, eta_nli)
    return n_channels * symbol_rate_baud * np.log2(1.0 + snr)


def _span_accumulation_factor(fiber: FiberSpec, span_length_km: float,
                              n_spans: int) -> float:
    """``sum_{k=1..N} eta_span**(N-k)`` -- Raman accumulated across un-amplified spans."""
    eta_span = fiber.transmissivity(span_length_km)
    return float(sum(eta_span ** (n_spans - k) for k in range(1, n_spans + 1)))


def multispan_raman_background_yield(launch_dbm_per_channel: float, n_channels: int,
                                     span_length_km: float, n_spans: int, *,
                                     fiber: FiberSpec = SMF28,
                                     raman: RamanModel | None = None,
                                     detector_efficiency: float = 0.5) -> float:
    """DV detector background yield (per gate) accumulated over ``n_spans`` spans.

    Each span injects the same single-span Raman generation (classical power is
    restored to launch by the inline amp); the contribution from span ``k`` is
    attenuated by the remaining ``N-k`` un-amplified spans before the receiver.
    """
    raman = raman or RamanModel()
    p_ch_w = 1e-3 * 10.0 ** (launch_dbm_per_channel / 10.0)
    p_total = p_ch_w * n_channels
    l_eff = fiber.effective_length_km(span_length_km)
    p_raman_span = (p_total * raman.raman_coeff_per_km_per_nm
                    * raman.filter_bandwidth_nm * l_eff)
    accum = _span_accumulation_factor(fiber, span_length_km, n_spans)
    nu = _C_M_PER_S / (raman.quantum_wavelength_nm * 1e-9)
    photon_energy = _PLANCK_J_S * nu
    photons_per_gate = p_raman_span / photon_energy * raman.gate_time_s * accum
    return photons_per_gate * detector_efficiency


def multispan_raman_photon_occupation(launch_dbm_per_channel: float, n_channels: int,
                                      span_length_km: float, n_spans: int, *,
                                      fiber: FiberSpec = SMF28,
                                      raman: RamanModel | None = None) -> float:
    """Mean Raman noise-photon occupation per mode, accumulated over spans."""
    raman = raman or RamanModel()
    p_ch_w = 1e-3 * 10.0 ** (launch_dbm_per_channel / 10.0)
    p_total = p_ch_w * n_channels
    l_eff = fiber.effective_length_km(span_length_km)
    p_raman_span = (p_total * raman.raman_coeff_per_km_per_nm
                    * raman.filter_bandwidth_nm * l_eff)
    accum = _span_accumulation_factor(fiber, span_length_km, n_spans)
    lam_m = raman.quantum_wavelength_nm * 1e-9
    photon_energy = _PLANCK_J_S * (_C_M_PER_S / lam_m)
    filter_bw_hz = (_C_M_PER_S / lam_m ** 2) * (raman.filter_bandwidth_nm * 1e-9)
    return p_raman_span * accum / (photon_energy * filter_bw_hz)


def multispan_dv_key_rate(launch_dbm_per_channel: float, n_channels: int,
                          span_length_km: float, n_spans: int, *,
                          fiber: FiberSpec = SMF28,
                          detector: DetectorModel | None = None,
                          raman: RamanModel | None = None,
                          mu: float = 0.5) -> float:
    """DV-QKD key rate over an amplified multi-span link (un-amplified quantum)."""
    detector = detector or DetectorModel()
    bg = multispan_raman_background_yield(
        launch_dbm_per_channel, n_channels, span_length_km, n_spans,
        fiber=fiber, raman=raman, detector_efficiency=detector.efficiency)
    eta = fiber.transmissivity(span_length_km * n_spans)   # full end-to-end loss
    return bb84_decoy_key_rate(eta, mu, detector=detector, background_yield=bg)


def multispan_cv_key_rate(launch_dbm_per_channel: float, n_channels: int,
                          span_length_km: float, n_spans: int, *,
                          fiber: FiberSpec = SMF28,
                          cv_detector: CVDetector | None = None,
                          raman: RamanModel | None = None,
                          modulation_variance: float = 4.0,
                          intrinsic_excess_noise: float = 0.01) -> float:
    """CV-QKD key rate over an amplified multi-span link (un-amplified quantum)."""
    n_bar = multispan_raman_photon_occupation(
        launch_dbm_per_channel, n_channels, span_length_km, n_spans,
        fiber=fiber, raman=raman)
    eta = fiber.transmissivity(span_length_km * n_spans)   # full end-to-end loss
    # Input-referred excess noise with homodyne polarization selection:
    # xi_R = 2 * (n_bar / 2) / eta = n_bar / eta  (see cv_raman_excess_noise).
    xi_raman = n_bar / eta if eta > 0.0 else float("inf")
    return cvqkd_homodyne_key_rate(
        eta, modulation_variance=modulation_variance,
        excess_noise=intrinsic_excess_noise + xi_raman, detector=cv_detector)
