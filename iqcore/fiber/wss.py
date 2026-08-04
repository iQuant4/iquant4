"""Wavelength-selective switches and ROADMs: routing, and the price of routing.

A long-haul or metro network is not one fiber end to end -- it is a chain of
**reconfigurable optical add/drop multiplexers (ROADMs)**, each built from
**wavelength-selective switches (WSS)** that route every channel independently:
express it through, drop it to a local receiver, or add a new one.  That
flexibility has a physical cost, and this module models both sides:

* **The passband.** A WSS channel filter is a flat-top **super-Gaussian**,
  ``T(f) = exp(-ln2 * (2 df / B_3dB)^(2*order))`` -- order 1 is an ordinary
  Gaussian, higher orders approach a brick wall.  Each pass adds insertion loss.
* **Filter narrowing.** Cascading ``k`` such filters multiplies their transfer
  functions, so the effective passband shrinks as
  ``B_eff = B_3dB * (1/k)^(1/(2*order))``.  After a handful of ROADMs the
  passband can be narrower than the signal itself.
* **The narrowing penalty.** When the occupied signal bandwidth (set by the
  symbol rate and the pulse-shaping roll-off, :mod:`iq4comm.dsp.pulse_shaping`)
  approaches the narrowed passband, the filter clips the signal's spectral
  wings; the lost power is an OSNR penalty, computed here by integrating the
  signal spectrum through the cascaded filter.

The routing side is modelled on the existing :class:`~iqcore.fiber.WDMComb`: a
:class:`Roadm` takes a comb and a set of drop/add instructions and returns the
expressed comb (with insertion loss applied) plus the dropped channels -- so a
multi-node lightpath can be assembled and its end-to-end penalty read off.

References: cascaded-WSS filter narrowing, e.g. Filer & Tibuleac, JLT 2012;
Pulikkaseril et al., Opt. Express 2011.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from math import log, log2

import numpy as np

from .wdm import WDMChannel, WDMComb

__all__ = [
    "WSSFilter",
    "cascaded_bandwidth_3db_ghz",
    "filter_narrowing_penalty_db",
    "Roadm",
    "RouteResult",
    "Lightpath",
    "lightpath_penalty_db",
]


@dataclass(frozen=True)
class WSSFilter:
    """A wavelength-selective-switch channel passband (super-Gaussian)."""

    bandwidth_3db_ghz: float = 40.0
    order: int = 3                       # 1 = Gaussian; higher = flatter top
    insertion_loss_db: float = 5.0

    def __post_init__(self) -> None:
        if self.bandwidth_3db_ghz <= 0:
            raise ValueError("bandwidth_3db_ghz must be > 0")
        if self.order < 1:
            raise ValueError("order must be >= 1")

    def transfer(self, df_hz: float | np.ndarray) -> np.ndarray:
        """Power transmission at frequency offset ``df`` from the channel centre.

        Normalised so ``T = 0.5`` (−3 dB) at ``df = B_3dB/2``.
        """
        b_hz = self.bandwidth_3db_ghz * 1e9
        x = 2.0 * np.abs(df_hz) / b_hz
        return np.exp(-log(2.0) * x ** (2 * self.order))

    def transfer_db(self, df_hz: float | np.ndarray) -> np.ndarray:
        return 10.0 * np.log10(self.transfer(df_hz))


def cascaded_bandwidth_3db_ghz(wss: WSSFilter, n_filters: int) -> float:
    """Effective −3 dB passband after ``n_filters`` identical cascaded WSS.

    ``B_eff = B_3dB * (1/k)^(1/(2*order))`` -- the passband narrows with each pass.
    """
    if n_filters < 1:
        raise ValueError("n_filters must be >= 1")
    return wss.bandwidth_3db_ghz * (1.0 / n_filters) ** (1.0 / (2 * wss.order))


def filter_narrowing_penalty_db(wss: WSSFilter, n_filters: int,
                                signal_bandwidth_hz: float, *,
                                n_points: int = 2001) -> float:
    """OSNR penalty (dB) from ``n_filters`` cascaded WSS clipping the signal.

    Integrates a flat signal spectrum of width ``signal_bandwidth_hz`` (the
    occupied bandwidth, e.g. ``Rs*(1+beta)`` from the pulse shaper) through the
    cascaded super-Gaussian and returns ``-10*log10(passed_fraction)``.  A wider
    roll-off or a narrower passband raises the penalty.
    """
    if n_filters < 1:
        raise ValueError("n_filters must be >= 1")
    half = 0.5 * signal_bandwidth_hz
    f = np.linspace(-half, half, n_points)
    t_cascade = wss.transfer(f) ** n_filters
    # Trapezoidal integral of the passed fraction, written out so it does not
    # depend on np.trapz / np.trapezoid (whose name differs across numpy versions).
    dx = f[1] - f[0]
    integral = (t_cascade.sum() - 0.5 * (t_cascade[0] + t_cascade[-1])) * dx
    passed = integral / (2.0 * half)
    if passed <= 0:
        return float("inf")
    return -10.0 * np.log10(passed)


@dataclass(frozen=True)
class RouteResult:
    """Output of routing a comb through one ROADM."""

    express: WDMComb          # channels passing through (insertion loss applied)
    dropped: WDMComb          # channels dropped to local receivers


@dataclass(frozen=True)
class Roadm:
    """A reconfigurable optical add/drop multiplexer built from WSS pairs.

    An express channel traverses two WSS stages (ingress + egress), so it takes
    ``2 * wss.insertion_loss_db``; a dropped or added channel traverses one.
    """

    wss: WSSFilter = WSSFilter()
    name: str = "ROADM"

    def route(self, comb: WDMComb, *, drop_indices: tuple[int, ...] = (),
              add_channels: tuple[WDMChannel, ...] = ()) -> RouteResult:
        """Express, drop and add channels, applying WSS insertion loss.

        ``drop_indices`` index into ``comb.channels``; ``add_channels`` are
        injected at their stated power (one WSS stage of loss applied to each).
        """
        drop = set(drop_indices)
        il_express = 10.0 ** (-2.0 * self.wss.insertion_loss_db / 10.0)
        il_add = 10.0 ** (-self.wss.insertion_loss_db / 10.0)

        express, dropped = [], []
        for i, ch in enumerate(comb.channels):
            if i in drop:
                dropped.append(ch)
            else:
                express.append(replace(ch, power_w=ch.power_w * il_express))
        for ch in add_channels:
            express.append(replace(ch, power_w=ch.power_w * il_add))
        express.sort(key=lambda c: c.frequency_hz)
        return RouteResult(WDMComb(express), WDMComb(dropped))


@dataclass(frozen=True)
class Lightpath:
    """An end-to-end route across a number of ROADM nodes."""

    n_nodes: int                          # ROADMs traversed (incl. add + drop)
    wss: WSSFilter = WSSFilter()

    @property
    def n_filter_stages(self) -> int:
        """WSS filtering stages a channel sees: add + (n_nodes-1) express + drop."""
        return self.n_nodes + 1

    @property
    def insertion_loss_db(self) -> float:
        """Total WSS insertion loss: two stages per express node, one each end."""
        express_nodes = max(0, self.n_nodes - 2)
        stages = 2 * express_nodes + 2      # add(1) + express(2 each) + drop(1)
        return stages * self.wss.insertion_loss_db

    def effective_bandwidth_ghz(self) -> float:
        return cascaded_bandwidth_3db_ghz(self.wss, self.n_filter_stages)

    def narrowing_penalty_db(self, signal_bandwidth_hz: float) -> float:
        return filter_narrowing_penalty_db(self.wss, self.n_filter_stages,
                                           signal_bandwidth_hz)


def lightpath_penalty_db(n_nodes: int, signal_bandwidth_hz: float, *,
                         wss: WSSFilter | None = None) -> dict:
    """Summary of the penalties a lightpath accrues across ``n_nodes`` ROADMs.

    Returns a dict with the effective passband, filter-narrowing penalty, total
    insertion loss, and whether the signal still fits (passband > signal BW).
    """
    lp = Lightpath(n_nodes, wss or WSSFilter())
    b_eff = lp.effective_bandwidth_ghz()
    return {
        "n_filter_stages": lp.n_filter_stages,
        "effective_bandwidth_ghz": b_eff,
        "narrowing_penalty_db": lp.narrowing_penalty_db(signal_bandwidth_hz),
        "insertion_loss_db": lp.insertion_loss_db,
        "signal_fits": b_eff * 1e9 > signal_bandwidth_hz,
    }
