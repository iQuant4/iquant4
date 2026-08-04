"""Roll-off as a dial between classical capacity and QKD secret-key rate.

This closes the loop between the pulse-shaping layer
(:mod:`iq4comm.dsp.pulse_shaping`) and the quantum-classical coexistence layer
(:mod:`iq4comm.qkd.coexistence`).  The chain is:

    roll-off beta  ->  channel spacing  ->  channels that fit a fixed optical band
                   ->  aggregate classical capacity   (rises as beta falls)
                   ->  total launch power              (rises as beta falls)
                   ->  spontaneous-Raman background    (rises with total power)
                   ->  QKD secret-key rate             (falls as beta falls)

So at a *fixed per-channel launch power* and a *fixed optical band*, the roll-off
is a single design knob that trades aggregate classical throughput against the
co-propagating quantum channel: tighter shaping (small beta) packs more channels
-- more bits/s -- but the extra channels raise the total power the quantum
channel must survive.  Because the GN nonlinear-interference term depends on the
*occupied optical band* (held roughly constant when you fill a fixed window), the
per-channel SNR is nearly beta-independent here; the tradeoff is dominated by the
channel count, not by per-channel penalty.

This is the platform's shared-foundation principle made concrete: one physical
description (fiber + shaping) drives the classical capacity and the quantum
key rate together, from the same numbers.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import floor, log10

from iqcore.fiber import FiberSpec, SMF28
from iq4comm.dsp.pulse_shaping import nyquist_channel_spacing_hz
from .format_impact import FEC_BER, format_capacity_bps
from .optimize import protocol_coexistence_key_rate

__all__ = [
    "channels_in_band",
    "GridFillPoint",
    "grid_fill_tradeoff",
    "best_rolloff_for_key_rate",
]


def channels_in_band(optical_band_hz: float, symbol_rate_baud: float, *,
                     shape: str = "rrc", beta: float = 0.2,
                     guard_fraction: float = 0.0) -> int:
    """How many channels of pulse-shape ``shape`` fit in an optical band.

    ``floor(optical_band / channel_spacing)`` where the spacing is the Nyquist
    spacing of the shape (``Rs*(1+beta)`` for RRC/RC, plus any guard band).
    """
    spacing = nyquist_channel_spacing_hz(shape, symbol_rate_baud, beta=beta,
                                         guard_fraction=guard_fraction)
    return max(0, int(floor(optical_band_hz / spacing)))


@dataclass(frozen=True)
class GridFillPoint:
    """One roll-off operating point on a fixed optical band."""

    beta: float
    channel_spacing_hz: float
    n_channels: int
    launch_dbm_per_channel: float
    total_launch_dbm: float
    classical_capacity_bps: float
    classical_closes: bool
    secret_key_rate: float

    @property
    def capacity_tbps(self) -> float:
        return self.classical_capacity_bps / 1e12


def grid_fill_tradeoff(distance_km: float, optical_band_hz: float,
                       launch_dbm_per_channel: float, *,
                       rolloffs=(0.01, 0.05, 0.1, 0.2, 0.35, 0.5, 0.75, 1.0),
                       fmt: str = "16QAM", shape: str = "rrc",
                       guard_fraction: float = 0.0, qkd_protocol: str = "dv",
                       symbol_rate_baud: float = 32e9, fiber: FiberSpec = SMF28,
                       noise_figure_db: float = 5.0, min_ber: float = FEC_BER,
                       **qkd_kwargs) -> list[GridFillPoint]:
    """Sweep roll-off over a fixed optical band; return the capacity/QKD tradeoff.

    For each roll-off the spacing sets how many ``fmt`` channels fill
    ``optical_band_hz``; the aggregate classical capacity (if the link closes)
    is paired with the QKD secret-key rate at the resulting *total* launch power,
    so the classical-vs-quantum tradeoff of the shaping choice is explicit.
    """
    out = []
    for beta in rolloffs:
        spacing = nyquist_channel_spacing_hz(shape, symbol_rate_baud, beta=beta,
                                             guard_fraction=guard_fraction)
        n_ch = max(0, int(floor(optical_band_hz / spacing)))
        if n_ch == 0:
            out.append(GridFillPoint(beta, spacing, 0, launch_dbm_per_channel,
                                     float("-inf"), 0.0, False, 0.0))
            continue
        cap, _ber, closes = format_capacity_bps(
            fmt, launch_dbm_per_channel, n_ch, distance_km, min_ber=min_ber,
            fiber=fiber, symbol_rate_baud=symbol_rate_baud,
            channel_spacing_hz=spacing, noise_figure_db=noise_figure_db)
        qkd = protocol_coexistence_key_rate(
            qkd_protocol, distance_km, launch_dbm_per_channel, n_ch,
            fiber=fiber, **qkd_kwargs)
        total_dbm = launch_dbm_per_channel + 10.0 * log10(n_ch)
        out.append(GridFillPoint(beta, spacing, n_ch, launch_dbm_per_channel,
                                 total_dbm, cap, closes, qkd))
    return out


def best_rolloff_for_key_rate(distance_km: float, optical_band_hz: float,
                              launch_dbm_per_channel: float, min_key_rate: float,
                              *, rolloffs=(0.01, 0.05, 0.1, 0.2, 0.35, 0.5, 0.75, 1.0),
                              **kw) -> GridFillPoint | None:
    """Tightest roll-off (max capacity) that still meets a QKD key-rate floor.

    Returns the highest-capacity :class:`GridFillPoint` whose secret-key rate is
    at or above ``min_key_rate`` and whose classical link closes, or None if no
    roll-off in the sweep satisfies the constraint.
    """
    pts = grid_fill_tradeoff(distance_km, optical_band_hz, launch_dbm_per_channel,
                             rolloffs=rolloffs, **kw)
    feasible = [p for p in pts if p.classical_closes and p.secret_key_rate >= min_key_rate]
    if not feasible:
        return None
    return max(feasible, key=lambda p: p.classical_capacity_bps)
