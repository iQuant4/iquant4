"""Coherent DSP: carrier-phase and symbol-timing recovery.

A coherent receiver mixes the incoming field with a free-running local
oscillator, so before symbols can be decided the DSP must undo two impairments
the GN/BER model previously just assumed away:

* **Carrier recovery** — the transmit laser and the LO differ in frequency (a
  slowly varying *frequency offset*) and each has finite linewidth (a random
  *phase-noise* walk, variance ``2π·Δν·T_s`` per symbol). This module estimates
  and removes both: an M-th-power frequency-offset estimator, **Viterbi–Viterbi**
  carrier-phase estimation for M-PSK, and **blind phase search (BPS)** for QAM.
* **Timing recovery** — the ADC does not sample at the symbol centres. The
  **Gardner** timing-error detector gives the classic S-curve (zero at the
  correct instant), and the feed-forward **Oerder–Meyr** estimator recovers a
  fractional timing offset from the ``|x|²`` spectral line at the symbol rate.

These close the last gap in the coherent front-end: with them, the eye/EVM/BER
diagnostics operate on a recovered signal rather than an idealised one. All
estimators are feed-forward and testable against a known injected impairment.

References: Viterbi & Viterbi, IEEE-IT 1983; Pfau et al. (BPS), JLT 2009;
Gardner, IEEE-COM 1986; Oerder & Meyr, IEEE-COM 1988.
"""

from __future__ import annotations

from math import pi

import numpy as np

from iq4comm.modulation import get_constellation

__all__ = [
    "laser_phase_noise",
    "apply_frequency_offset",
    "estimate_frequency_offset",
    "viterbi_viterbi_cpe",
    "bps_cpe",
    "residual_phase_variance",
    "gardner_ted",
    "oerder_meyr_timing",
]


def laser_phase_noise(n_symbols: int, linewidth_hz: float, symbol_rate_baud: float,
                      rng: np.random.Generator) -> np.ndarray:
    """Wiener phase-noise walk (rad) for a combined Tx+LO linewidth.

    Increment variance per symbol is ``2π·Δν·T_s`` (the standard combined-linewidth
    result); returns the cumulative phase.
    """
    if linewidth_hz < 0 or symbol_rate_baud <= 0:
        raise ValueError("linewidth >= 0 and symbol_rate > 0 required")
    ts = 1.0 / symbol_rate_baud
    sigma = np.sqrt(2.0 * pi * linewidth_hz * ts)
    return np.cumsum(sigma * rng.standard_normal(n_symbols))


def apply_frequency_offset(symbols: np.ndarray, foffset_hz: float,
                           symbol_rate_baud: float) -> np.ndarray:
    """Multiply by ``exp(j 2π Δf n T_s)`` — a carrier frequency offset."""
    n = np.arange(len(symbols))
    return symbols * np.exp(1j * 2.0 * pi * foffset_hz * n / symbol_rate_baud)


def estimate_frequency_offset(symbols: np.ndarray, m: int,
                              symbol_rate_baud: float) -> float:
    """Estimate the carrier frequency offset (Hz) by the M-th-power method.

    Raising to the M-th power strips M-PSK data; the residual rotates at
    ``M·Δf``, recovered from the mean phase increment of consecutive samples.
    """
    z = symbols ** m
    dphi = np.angle(np.mean(z[1:] * np.conjugate(z[:-1])))
    return dphi * symbol_rate_baud / (2.0 * pi * m)


def _unwrap(phase: np.ndarray) -> np.ndarray:
    return np.unwrap(phase)


def viterbi_viterbi_cpe(symbols: np.ndarray, m: int = 4, window: int = 21
                        ) -> tuple[np.ndarray, np.ndarray]:
    """Viterbi–Viterbi carrier-phase estimation/compensation for M-PSK.

    Returns ``(compensated_symbols, phase_estimate)``. The data modulation is
    removed by the M-th power, the phase is averaged over ``window`` symbols and
    unwrapped, and the signal is de-rotated. A discrete M-fold phase ambiguity
    remains (resolved downstream by pilots/differential coding).
    """
    z = symbols ** m
    k = np.ones(window) / window
    zf = np.convolve(z, k, mode="same")
    phi = _unwrap(np.angle(zf)) / m
    return symbols * np.exp(-1j * phi), phi


def bps_cpe(symbols: np.ndarray, fmt: str, n_angles: int = 32, window: int = 21
            ) -> tuple[np.ndarray, np.ndarray]:
    """Blind-phase-search carrier recovery for QAM (and PSK).

    Tests ``n_angles`` trial rotations over the constellation's π/2 symmetry,
    picks per-symbol the angle minimising the windowed distance to the nearest
    constellation point, and de-rotates. Returns ``(compensated, phase_estimate)``.
    """
    const = get_constellation(fmt)
    pts = const.points
    angles = np.linspace(-pi / 4, pi / 4, n_angles, endpoint=False)
    r = np.asarray(symbols)
    # distance^2 to nearest constellation point for each (symbol, test-angle)
    rot = np.outer(r, np.exp(-1j * angles))                 # (N, A)
    d2 = np.min(np.abs(rot[:, :, None] - pts[None, None, :]) ** 2, axis=2)  # (N, A)
    # smooth the per-angle cost over the window, then pick the best angle
    kern = np.ones(window)
    cost = np.apply_along_axis(lambda c: np.convolve(c, kern, mode="same"), 0, d2)
    best = np.argmin(cost, axis=1)
    phi = angles[best]
    return r * np.exp(-1j * phi), phi


def residual_phase_variance(compensated: np.ndarray, reference: np.ndarray) -> float:
    """Variance of the residual phase *jitter* after carrier recovery.

    Data-aided: the residual ``angle(r·conj(s))`` carries a constant offset (the
    algorithm's deterministic bias and the discrete phase ambiguity) plus the
    tracking jitter we care about. The constant offset is removed by subtracting
    the *circular mean*, and the variance of what remains is the tracking error —
    independent of which ambiguity branch the recovery settled on.
    """
    res = np.angle(compensated * np.conjugate(reference))
    mean_angle = np.angle(np.mean(np.exp(1j * res)))         # circular mean
    jitter = np.angle(np.exp(1j * (res - mean_angle)))       # wrapped about the mean
    return float(np.var(jitter))


def gardner_ted(samples: np.ndarray, sps: int = 2) -> float:
    """Mean Gardner timing-error-detector value (2 samples/symbol).

    ``e_k = Re{ conj(x_mid) · (x_late − x_early) }`` averaged over symbols; ~0 at
    the correct sampling instant, and changing sign as the timing phase drifts —
    the classic S-curve when swept against a timing offset.
    """
    if sps < 2:
        raise ValueError("Gardner TED needs sps >= 2")
    x = np.asarray(samples)
    centers = np.arange(0, len(x) - sps, sps)                # symbol-centre indices
    if centers.size == 0:
        return 0.0
    early = x[centers]
    late = x[centers + sps]
    mid = x[centers + sps // 2]                              # half-symbol point
    e = np.real(np.conjugate(mid) * (late - early))
    return float(np.mean(e))


def oerder_meyr_timing(samples: np.ndarray, sps: int) -> float:
    """Feed-forward Oerder–Meyr fractional timing estimate (fraction of a symbol).

    The ``|x|²`` sequence has a spectral line at the symbol rate whose phase gives
    the timing offset: ``τ = −angle(Σ |x_n|² e^{−j2π n/sps}) / 2π`` (in symbols).
    """
    if sps < 2:
        raise ValueError("timing recovery needs sps >= 2")
    x = np.asarray(samples)
    n = np.arange(len(x))
    c = np.sum(np.abs(x) ** 2 * np.exp(-1j * 2.0 * pi * n / sps))
    return float((-np.angle(c) / (2.0 * pi)) % 1.0)
