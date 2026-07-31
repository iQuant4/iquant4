"""Gaussian-Noise (GN) model of nonlinear propagation.

The GN model treats the Kerr nonlinear interference (NLI) of a densely-loaded
WDM signal as additive Gaussian noise whose power scales with the *cube* of the
per-channel launch power.  Combined with the (launch-independent) ASE noise this
gives an effective SNR

    SNR(P) = P / (P_ASE + eta * P^3),

which has a maximum at the optimal launch power -- the "nonlinear Shannon limit"
that sets the real reach of an uncompensated coherent link.  This is what closes
the caveat in the ASE-only BER model: reach is now finite.

NLI coefficient (incoherent, N_s identical spans), center channel::

    eta = N_s * (8/27) * gamma^2 * L_eff^2
              * asinh( (pi^2/2) * |beta2| * L_eff_a * B_wdm^2 )
              / ( pi * |beta2| * L_eff_a * R_s^2 )

so that ``P_NLI = eta * P_ch^3``.  Units: beta2 in ps^2/km, lengths in km,
bandwidths in THz (1/ps); ``eta`` comes out in 1/W^2.

Reference: Poggiolini, "The GN Model of Non-Linear Propagation in Uncompensated
Coherent Optical Systems," J. Lightwave Technol. 30(24), 2012.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import asinh, pi

import numpy as np

from iqcore.fiber import Amplifier, FiberSpec

__all__ = [
    "nli_coefficient",
    "nli_power_w",
    "effective_snr",
    "optimal_launch_power_w",
    "ase_power_w",
    "GNOperatingPoint",
    "gn_operating_point",
]


def nli_coefficient(fiber: FiberSpec, span_length_km: float, n_spans: int,
                    symbol_rate_baud: float, wdm_bandwidth_hz: float, *,
                    wavelength_nm: float | None = None) -> float:
    """GN-model NLI coefficient ``eta`` (1/W^2) with ``P_NLI = eta * P_ch^3``.

    Incoherent accumulation (linear in ``n_spans``); center-channel, Nyquist-WDM
    approximation (channel noise bandwidth ~ ``symbol_rate``).
    """
    if n_spans < 1:
        raise ValueError("n_spans must be >= 1")
    gamma = fiber.gamma_per_w_per_km
    alpha_p = fiber.alpha_neper_per_km               # power basis, 1/km
    l_eff = fiber.effective_length_km(span_length_km)
    l_eff_a = 1.0 / alpha_p if alpha_p > 0 else span_length_km
    b2 = abs(fiber.beta2_ps2_per_km(wavelength_nm))   # ps^2/km
    b_wdm_thz = wdm_bandwidth_hz / 1e12               # 1/ps
    r_s_thz = symbol_rate_baud / 1e12                 # 1/ps
    if b2 == 0.0:
        # Zero dispersion: asinh argument -> the phased-array limit; fall back to
        # a small-but-finite dispersion is out of scope, so guard against /0.
        raise ValueError("GN model requires non-zero dispersion (|beta2| > 0)")

    arg = (pi ** 2 / 2.0) * b2 * l_eff_a * b_wdm_thz ** 2
    numer = (8.0 / 27.0) * gamma ** 2 * l_eff ** 2 * asinh(arg)
    denom = pi * b2 * l_eff_a * r_s_thz ** 2
    return n_spans * numer / denom


def nli_power_w(eta: float, p_ch_w: float) -> float:
    """Nonlinear-interference power in the channel: ``eta * P_ch^3``."""
    return eta * p_ch_w ** 3


def ase_power_w(amplifier: Amplifier, n_spans: int, symbol_rate_baud: float, *,
                polarizations: int = 1) -> float:
    """Accumulated ASE power in the channel bandwidth for ``n_spans`` amplifiers.

    Uses the signal-copolarised ASE (``polarizations=1``) by default, matching
    the single-polarisation SNR convention used with :func:`effective_snr`.
    """
    per_amp = amplifier.ase_power_w(symbol_rate_baud, polarizations=polarizations)
    return n_spans * per_amp


def effective_snr(p_ch_w: float, ase_power_w: float, eta: float) -> float:
    """Effective linear SNR ``P / (P_ASE + eta P^3)``."""
    if p_ch_w <= 0:
        raise ValueError("p_ch_w must be positive")
    return p_ch_w / (ase_power_w + eta * p_ch_w ** 3)


def optimal_launch_power_w(ase_power_w: float, eta: float) -> float:
    """Launch power maximising :func:`effective_snr` (closed form).

    Setting ``d/dP [P / (A + eta P^3)] = 0`` gives ``A = 2 eta P^3``, i.e. the NLI
    is half the ASE at the optimum: ``P_opt = (A / (2 eta))^(1/3)``.
    """
    if eta <= 0:
        raise ValueError("eta must be positive")
    return (ase_power_w / (2.0 * eta)) ** (1.0 / 3.0)


@dataclass(frozen=True)
class GNOperatingPoint:
    """The GN optimum for a link configuration."""

    optimal_launch_dbm: float
    max_snr_db: float
    ase_power_w: float
    nli_power_w: float
    eta: float
    total_length_km: float

    @property
    def nli_to_ase_ratio(self) -> float:
        return self.nli_power_w / self.ase_power_w


def gn_operating_point(fiber: FiberSpec, span_length_km: float, n_spans: int,
                       amplifier: Amplifier, symbol_rate_baud: float,
                       wdm_bandwidth_hz: float, *,
                       wavelength_nm: float | None = None) -> GNOperatingPoint:
    """Optimal launch power and peak SNR for an ``n_spans`` link (GN model)."""
    eta = nli_coefficient(fiber, span_length_km, n_spans, symbol_rate_baud,
                          wdm_bandwidth_hz, wavelength_nm=wavelength_nm)
    p_ase = ase_power_w(amplifier, n_spans, symbol_rate_baud)
    p_opt = optimal_launch_power_w(p_ase, eta)
    snr = effective_snr(p_opt, p_ase, eta)
    return GNOperatingPoint(
        optimal_launch_dbm=10.0 * np.log10(p_opt * 1e3),
        max_snr_db=10.0 * np.log10(snr),
        ase_power_w=p_ase,
        nli_power_w=nli_power_w(eta, p_opt),
        eta=eta,
        total_length_km=n_spans * span_length_km,
    )
