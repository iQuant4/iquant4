"""Joint classical-quantum coexistence optimizer.

Turns the coexistence *calculator* into a design *tool*: given a fiber route, a
DWDM channel plan, and a quantum-security requirement, it solves for the best
classical launch power instead of sweeping by hand.

Because classical capacity is unimodal in launch power (it rises to the
Gaussian-Noise optimum, then falls) while the QKD key rate is monotonically
decreasing in launch power, the constrained optimum is simply::

    p* = min( p_GN-optimum , p_secure-boundary )

i.e. push the classical power up to its own optimum, unless QKD security forces
you to back off first.  This module finds both points (via SciPy) and returns
the operating point plus whether the QKD constraint binds.  A gradient-based
(autodiff) optimizer over more variables is the natural future upgrade.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy.optimize import brentq, minimize_scalar

from iqcore.fiber import FiberSpec, SMF28
from .dv import DetectorModel
from .cv import CVDetector
from .coexistence import (
    RamanModel, classical_capacity_bps,
    coexistence_dv_key_rate, coexistence_cv_key_rate,
)

__all__ = ["OperatingPoint", "optimize_launch_power", "coexistence_reach"]


@dataclass(frozen=True)
class OperatingPoint:
    """Result of a coexistence optimization."""

    feasible: bool
    launch_dbm: float
    classical_capacity_bps: float
    secret_key_rate: float
    qkd_constraint_binds: bool
    distance_km: float
    n_channels: int
    protocol: str

    @property
    def capacity_tbps(self) -> float:
        return self.classical_capacity_bps / 1e12


def _key_rate_fn(protocol: str, fiber, detector, cv_detector, raman):
    proto = protocol.lower()
    if proto == "dv":
        return lambda d, p, n: coexistence_dv_key_rate(
            d, p, n, fiber=fiber, detector=detector, raman=raman)
    if proto == "cv":
        return lambda d, p, n: coexistence_cv_key_rate(
            d, p, n, fiber=fiber, cv_detector=cv_detector, raman=raman)
    raise ValueError("protocol must be 'dv' or 'cv'")


def optimize_launch_power(distance_km: float, n_channels: int,
                          min_key_rate: float, *, protocol: str = "dv",
                          fiber: FiberSpec = SMF28,
                          detector: DetectorModel | None = None,
                          cv_detector: CVDetector | None = None,
                          raman: RamanModel | None = None,
                          symbol_rate_baud: float = 32e9,
                          channel_spacing_hz: float = 50e9,
                          power_bounds_dbm: tuple[float, float] = (-30.0, 10.0)
                          ) -> OperatingPoint:
    """Maximise classical capacity subject to secret-key rate >= ``min_key_rate``.

    Returns an :class:`OperatingPoint`; ``feasible`` is False if no launch power
    in ``power_bounds_dbm`` meets the key-rate requirement.
    """
    key_rate = _key_rate_fn(protocol, fiber, detector, cv_detector, raman)
    lo, hi = power_bounds_dbm

    def cap(pdbm):
        return classical_capacity_bps(
            pdbm, n_channels, distance_km, fiber=fiber,
            symbol_rate_baud=symbol_rate_baud, channel_spacing_hz=channel_spacing_hz)

    # Unconstrained capacity optimum (GN optimum) over the power range.
    gn = minimize_scalar(lambda p: -cap(p), bounds=(lo, hi), method="bounded")
    p_gn = float(gn.x)

    # Secure boundary: largest launch power with key rate >= threshold.
    def margin(pdbm):
        return key_rate(distance_km, pdbm, n_channels) - min_key_rate

    if margin(lo) < 0:                       # even minimal power is insecure
        return OperatingPoint(False, float("nan"), 0.0, 0.0, True,
                              distance_km, n_channels, protocol)
    if margin(hi) >= 0:                       # secure across the whole range
        p_sec = hi
    else:
        p_sec = float(brentq(margin, lo, hi, xtol=1e-4))

    binds = p_sec < p_gn
    p_star = min(p_gn, p_sec)
    return OperatingPoint(
        True, p_star, cap(p_star), key_rate(distance_km, p_star, n_channels),
        binds, distance_km, n_channels, protocol)


def coexistence_reach(n_channels: int, min_key_rate: float,
                      min_capacity_bps: float, *, protocol: str = "dv",
                      fiber: FiberSpec = SMF28,
                      detector: DetectorModel | None = None,
                      cv_detector: CVDetector | None = None,
                      raman: RamanModel | None = None,
                      symbol_rate_baud: float = 32e9,
                      channel_spacing_hz: float = 50e9,
                      max_distance_km: float = 200.0) -> float:
    """Maximum distance (km) where some launch power meets BOTH a capacity and a
    key-rate target simultaneously.  Returns 0.0 if infeasible even at 0 km."""
    def feasible(d):
        op = optimize_launch_power(
            d, n_channels, min_key_rate, protocol=protocol, fiber=fiber,
            detector=detector, cv_detector=cv_detector, raman=raman,
            symbol_rate_baud=symbol_rate_baud, channel_spacing_hz=channel_spacing_hz)
        return op.feasible and op.classical_capacity_bps >= min_capacity_bps

    if not feasible(1.0):
        return 0.0
    # Bisect for the crossover distance.
    lo, hi = 1.0, max_distance_km
    if feasible(hi):
        return max_distance_km
    for _ in range(40):
        mid = 0.5 * (lo + hi)
        if feasible(mid):
            lo = mid
        else:
            hi = mid
    return lo
