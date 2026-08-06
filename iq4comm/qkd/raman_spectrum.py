"""Wavelength-resolved spontaneous-Raman coexistence noise.

The scalar :class:`~iq4comm.qkd.coexistence.RamanModel` uses a single effective
in-band coefficient ``rho`` calibrated to the C-band operating point of
Ferreira da Silva *et al.* (JLT 2014).  That is accurate for a quantum channel sitting *inside* the
classical C-band comb (small pump-quantum offset), but it cannot predict what
happens when the quantum channel is moved far from the pump -- e.g. an O-band
(1310 nm) quantum channel co-propagating with C-band (1550 nm) DWDM -- because
the spontaneous-Raman scattering efficiency is strongly frequency-offset
dependent.

This module adds that offset dependence.  The spontaneous-Raman noise photon
flux scattered from a classical channel into the quantum channel scales as

    rho(dnu, sign)  ~  g_R(|dnu|) * Phi_sign(|dnu|, T)

where

* ``g_R(|dnu|)`` is the (normalised) silica Raman gain spectrum -- a damped
  harmonic-oscillator model (Blow & Wood 1989; Agrawal, *Nonlinear Fiber
  Optics*), rising from zero at zero offset, peaking near 13.2 THz, and falling
  off beyond ~30 THz; and
* ``Phi_sign`` is the thermal phonon-population factor, ``n_th + 1`` for Stokes
  (classical at higher optical frequency than the quantum channel) and ``n_th``
  for anti-Stokes (classical at lower frequency), with the Bose-Einstein
  occupation ``n_th(dnu, T) = 1 / (exp(h |dnu| / kT) - 1)``.

The absolute scale is anchored so that a representative in-band C-band offset
reproduces the calibrated scalar coefficient ``rho = 2.5e-8 /(km*nm)``.  Every
other offset -- in particular the large O-band offset -- is then a *prediction*
of the spectral profile, not a second free parameter.

For a multi-channel comb the total noise is the vector sum over channels,
``sum_i rho(nu_i - nu_q) * P_i`` -- the wavelength-resolved ``r^T P`` model.

References
----------
* A. R. Chraplyvy; R. H. Stolen; Blow & Wood, IEEE JQE 25, 2665 (1989).
* G. P. Agrawal, *Nonlinear Fiber Optics*, silica Raman response (tau1=12.2 fs,
  tau2=32 fs).
* P. D. Townsend, Eraerds *et al.*, NJP 12, 063027 (2010) (O-band vs C-band
  coexistence noise, order-of-magnitude cross-check).
* T. Ferreira da Silva *et al.*, JLT 32, 2332 (2014) (C-band anchor).
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

_PLANCK_J_S = 6.62607015e-34
_BOLTZMANN_J_PER_K = 1.380649e-23
_C_M_PER_S = 2.99792458e8

# Silica Raman response time constants (Agrawal / Blow & Wood).
_TAU1_S = 12.2e-15
_TAU2_S = 32.0e-15

# In-band C-band anchor: representative power-weighted pump-quantum offset of the
# da Silva et al. comb (classical channels spanning -1.2..+1.4 THz around the
# 1546.12 nm quantum channel) and the calibrated scalar coefficient it maps to.
ANCHOR_OFFSET_HZ = 0.8e12
ANCHOR_RHO_PER_KM_PER_NM = 2.5e-8
ROOM_TEMPERATURE_K = 300.0


def silica_raman_gain(delta_nu_hz: float | np.ndarray) -> float | np.ndarray:
    """Normalised silica Raman gain profile ``g_R(|dnu|)`` (peak = 1).

    Damped-harmonic-oscillator (single-Lorentzian) model of the silica Raman
    response.  ``delta_nu_hz`` is the optical-frequency offset (Hz); the profile
    depends only on its magnitude.  Rises ~linearly from zero, peaks near
    13.2 THz, and falls off as the offset grows.
    """
    w = 2.0 * np.pi * np.abs(np.asarray(delta_nu_hz, dtype=float))
    inv = 1.0 / _TAU1_S ** 2 + 1.0 / _TAU2_S ** 2
    damp = 2.0 * w / _TAU2_S
    raw = damp / ((inv - w ** 2) ** 2 + damp ** 2)
    # Peak of raw over frequency, for normalisation to unit peak.
    wgrid = 2.0 * np.pi * np.linspace(0.1e12, 40e12, 20000)
    dg = (2.0 * wgrid / _TAU2_S)
    rawgrid = dg / ((inv - wgrid ** 2) ** 2 + dg ** 2)
    peak = rawgrid.max()
    out = raw / peak
    return float(out) if np.isscalar(delta_nu_hz) else out


def phonon_occupation(delta_nu_hz: float | np.ndarray,
                      temperature_k: float = ROOM_TEMPERATURE_K) -> float | np.ndarray:
    """Bose-Einstein thermal phonon occupation ``n_th(|dnu|, T)``."""
    x = _PLANCK_J_S * np.abs(np.asarray(delta_nu_hz, dtype=float)) / (
        _BOLTZMANN_J_PER_K * temperature_k)
    # Guard the dnu->0 limit (n_th -> kT/h dnu diverges); clamp tiny offsets.
    x = np.maximum(x, 1e-9)
    out = 1.0 / np.expm1(x)
    return float(out) if np.isscalar(delta_nu_hz) else out


def spontaneous_raman_efficiency(delta_nu_hz: float,
                                 temperature_k: float = ROOM_TEMPERATURE_K) -> float:
    """Relative spontaneous-Raman scattering efficiency ``g_R * Phi_sign``.

    ``delta_nu_hz = nu_classical - nu_quantum``.  Positive offset (classical at
    higher optical frequency) is a Stokes process for light reaching the quantum
    channel and carries the ``n_th + 1`` factor; negative offset is anti-Stokes
    and carries ``n_th``.  Returned value is relative (unnormalised); use
    :func:`band_raman_coefficient` for an absolute, anchored coefficient.
    """
    g = silica_raman_gain(delta_nu_hz)
    n_th = phonon_occupation(delta_nu_hz, temperature_k)
    phi = (n_th + 1.0) if delta_nu_hz >= 0.0 else n_th
    return float(g * phi)


def _nm_to_hz(wavelength_nm: float) -> float:
    return _C_M_PER_S / (wavelength_nm * 1e-9)


def band_raman_coefficient(quantum_nm: float, classical_nm: float, *,
                           temperature_k: float = ROOM_TEMPERATURE_K,
                           anchor_rho: float = ANCHOR_RHO_PER_KM_PER_NM) -> float:
    """Effective Raman coefficient ``rho`` (1/(km*nm)) for a pump-quantum pair.

    Anchored so that a representative in-band C-band offset
    (:data:`ANCHOR_OFFSET_HZ`, Stokes) reproduces ``anchor_rho``.  The value for
    any other quantum/classical wavelength pair is a prediction of the spectral
    profile.  ``delta_nu = nu_classical - nu_quantum`` sets the Stokes/anti-Stokes
    branch automatically.
    """
    dnu = _nm_to_hz(classical_nm) - _nm_to_hz(quantum_nm)
    eff = spontaneous_raman_efficiency(dnu, temperature_k)
    anchor_eff = spontaneous_raman_efficiency(ANCHOR_OFFSET_HZ, temperature_k)
    return anchor_rho * eff / anchor_eff


@dataclass(frozen=True)
class ClassicalChannel:
    """A single co-propagating classical channel."""
    wavelength_nm: float
    power_w: float


def resolved_raman_rho_effective(quantum_nm: float,
                                 channels: list[ClassicalChannel], *,
                                 temperature_k: float = ROOM_TEMPERATURE_K,
                                 anchor_rho: float = ANCHOR_RHO_PER_KM_PER_NM) -> float:
    """Power-weighted effective ``rho`` for a comb of classical channels.

    Implements the wavelength-resolved ``r^T P / (1^T P)`` reduction: each
    channel contributes ``rho(nu_i - nu_q) * P_i`` and the effective coefficient
    is the total divided by the total classical power.  For a scalar-model
    comparison this is the number to feed the existing coexistence engine.
    """
    total_p = sum(c.power_w for c in channels)
    if total_p <= 0.0:
        return 0.0
    weighted = sum(
        band_raman_coefficient(quantum_nm, c.wavelength_nm,
                               temperature_k=temperature_k, anchor_rho=anchor_rho)
        * c.power_w
        for c in channels)
    return weighted / total_p


# Convenience band centres.
C_BAND_CENTER_NM = 1550.0
O_BAND_CENTER_NM = 1310.0
