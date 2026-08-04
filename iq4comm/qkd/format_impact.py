"""How the classical modulation format affects a co-propagating QKD channel.

The quantum channel's dominant coexistence impairment -- spontaneous Raman
scattering -- depends on the *average* classical power, not on the modulation
format.  So at a fixed launch power the format does not change the QKD key rate
directly.  The format matters *indirectly*: a higher-order format (16-/64-QAM)
needs a higher SNR to close the classical link at a given reach, which forces a
higher launch power, which raises the Raman floor and lowers the QKD rate.

This module exposes that coupling: for each format it computes the classical
capacity achievable at a launch power (via the GN-model SNR and the closed-form
BER), and pairs it with the (format-independent) QKD key rate at that power, so
one can read off the capacity-vs-secret-key tradeoff and the minimum launch each
format demands.

Note: this captures the *power-mediated* coupling.  A second-order direct effect
-- the modulation-format correction to the nonlinear-interference variance
(EGN model) -- is not included and is a natural refinement.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy.optimize import brentq

from iqcore.fiber import Amplifier, FiberSpec, SMF28
from iq4comm.dsp import ber_theory
from iq4comm.dsp.gn_model import nli_coefficient, ase_power_w, effective_snr
from iq4comm.dsp.fec import FECCode
from iq4comm.modulation import get_constellation
from .optimize import protocol_coexistence_key_rate

__all__ = [
    "channel_snr_db",
    "format_ber",
    "format_capacity_bps",
    "minimum_launch_for_format_dbm",
    "FormatImpact",
    "format_qkd_tradeoff",
]

FEC_BER = 3.8e-3  # 7% hard-decision FEC threshold


def channel_snr_db(launch_dbm_per_channel: float, n_channels: int,
                   distance_km: float, *, fiber: FiberSpec = SMF28,
                   symbol_rate_baud: float = 32e9,
                   channel_spacing_hz: float = 50e9,
                   noise_figure_db: float = 5.0) -> float:
    """Effective per-channel SNR (dB) from the GN model over one span."""
    amp = Amplifier(gain_db=fiber.loss_db(distance_km), noise_figure_db=noise_figure_db)
    eta = nli_coefficient(fiber, distance_km, 1, symbol_rate_baud,
                          n_channels * channel_spacing_hz)
    p_ase = ase_power_w(amp, 1, symbol_rate_baud)
    p_ch = 1e-3 * 10.0 ** (launch_dbm_per_channel / 10.0)
    return 10.0 * np.log10(effective_snr(p_ch, p_ase, eta))


def format_ber(fmt: str, snr_db: float) -> float:
    """BER of ``fmt`` at an effective SNR (Es/N0), via Eb/N0 = SNR / bits/symbol."""
    k = get_constellation(fmt).bits_per_symbol
    ebn0_db = snr_db - 10.0 * np.log10(k)
    return ber_theory(fmt, ebn0_db)


def _close_threshold(min_ber: float, fec: FECCode | None) -> float:
    """Pre-FEC BER a channel must beat to 'close': a code's threshold, or ``min_ber``."""
    return fec.threshold_ber() if fec is not None else min_ber


def format_capacity_bps(fmt: str, launch_dbm_per_channel: float, n_channels: int,
                        distance_km: float, *, min_ber: float = FEC_BER,
                        fec: FECCode | None = None,
                        fiber: FiberSpec = SMF28, symbol_rate_baud: float = 32e9,
                        channel_spacing_hz: float = 50e9,
                        noise_figure_db: float = 5.0):
    """Net classical capacity (bits/s) delivered by ``fmt`` if it closes, else 0.

    With a :class:`~iq4comm.dsp.fec.FECCode`, the link "closes" when its channel
    BER is under that code's *computed* threshold (not the hard-coded 3.8e-3),
    and the returned capacity is the *net* information rate ``n*Rs*k*R`` -- the
    FEC overhead is charged honestly.  Without a code the legacy behaviour holds:
    close at ``min_ber`` and report the raw (pre-overhead) rate.

    Returns ``(capacity_bps, ber, closes)``.
    """
    snr = channel_snr_db(launch_dbm_per_channel, n_channels, distance_km,
                         fiber=fiber, symbol_rate_baud=symbol_rate_baud,
                         channel_spacing_hz=channel_spacing_hz,
                         noise_figure_db=noise_figure_db)
    ber = format_ber(fmt, snr)
    k = get_constellation(fmt).bits_per_symbol
    closes = ber <= _close_threshold(min_ber, fec)
    rate = fec.rate if fec is not None else 1.0
    capacity = n_channels * symbol_rate_baud * k * rate if closes else 0.0
    return capacity, ber, closes


def minimum_launch_for_format_dbm(fmt: str, n_channels: int, distance_km: float, *,
                                  min_ber: float = FEC_BER, fec: FECCode | None = None,
                                  fiber: FiberSpec = SMF28,
                                  symbol_rate_baud: float = 32e9,
                                  channel_spacing_hz: float = 50e9,
                                  noise_figure_db: float = 5.0,
                                  power_bounds_dbm: tuple[float, float] = (-30.0, 10.0)):
    """Lowest launch power (dBm/ch) at which ``fmt`` meets the BER target.

    With a :class:`~iq4comm.dsp.fec.FECCode` the target is that code's threshold,
    so a stronger code lets the format close at a *lower* launch power -- which,
    in coexistence, is exactly the power headroom handed back to the QKD channel.
    Returns None if the format never closes in ``power_bounds_dbm``.
    """
    lo, hi = power_bounds_dbm
    threshold = _close_threshold(min_ber, fec)

    def margin(p):
        return threshold - format_ber(fmt, channel_snr_db(
            p, n_channels, distance_km, fiber=fiber,
            symbol_rate_baud=symbol_rate_baud, channel_spacing_hz=channel_spacing_hz,
            noise_figure_db=noise_figure_db))

    # Scan for the first power where the format closes (margin >= 0).
    grid = np.linspace(lo, hi, 200)
    closed = [p for p in grid if margin(p) >= 0]
    if not closed:
        return None
    p_close = closed[0]
    if p_close <= lo + 1e-9:
        return lo
    return float(brentq(margin, lo, p_close, xtol=1e-3))


@dataclass(frozen=True)
class FormatImpact:
    fmt: str
    launch_dbm: float
    classical_capacity_bps: float
    classical_closes: bool
    secret_key_rate: float

    @property
    def capacity_tbps(self) -> float:
        return self.classical_capacity_bps / 1e12


def format_qkd_tradeoff(distance_km: float, n_channels: int,
                        launch_dbm_per_channel: float, *,
                        formats=("OOK", "QPSK", "16QAM", "64QAM"),
                        qkd_protocol: str = "dv", min_ber: float = FEC_BER,
                        fec: FECCode | None = None,
                        fiber: FiberSpec = SMF28, symbol_rate_baud: float = 32e9,
                        channel_spacing_hz: float = 50e9, noise_figure_db: float = 5.0,
                        **qkd_kwargs) -> list[FormatImpact]:
    """Per-format classical capacity paired with the QKD key rate at one launch.

    The QKD rate is computed once (it is format-independent for fixed power) and
    attached to every format, so the tradeoff is explicit: higher-order formats
    add classical capacity at the *same* QKD cost -- but only if the link SNR
    supports them at this launch power.
    """
    qkd = protocol_coexistence_key_rate(
        qkd_protocol, distance_km, launch_dbm_per_channel, n_channels,
        fiber=fiber, **qkd_kwargs)
    out = []
    for fmt in formats:
        cap, _ber, closes = format_capacity_bps(
            fmt, launch_dbm_per_channel, n_channels, distance_km, min_ber=min_ber,
            fec=fec, fiber=fiber, symbol_rate_baud=symbol_rate_baud,
            channel_spacing_hz=channel_spacing_hz, noise_figure_db=noise_figure_db)
        out.append(FormatImpact(fmt, launch_dbm_per_channel, cap, closes, qkd))
    return out
