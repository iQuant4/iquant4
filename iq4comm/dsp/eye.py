"""Eye diagrams and the Q-factor: reading link quality off the waveform.

BER is the ground truth, but you cannot always measure it directly (it is tiny,
and you would have to send 10^12 bits to see one error at 1e-12).  The **Q-factor**
is the standard proxy: it is estimated from the *statistics of the received
levels* -- the separation of the one/zero rails relative to their noise --

    Q = (mu1 - mu0) / (sigma1 + sigma0),   BER = 0.5 * erfc(Q / sqrt(2)),

so a Q measured over a few thousand symbols predicts a BER that would take hours
to count.  The **eye diagram** is the visual form of the same information: fold
the waveform into overlapping symbol windows and the vertical opening is the
noise margin, the horizontal opening is the timing margin, and the Q-factor is
read at the instant of maximum vertical opening.

This module sits directly on the pulse-shaping layer: :func:`shaped_nrz_waveform`
builds a realistic shaped, noisy NRZ waveform from :mod:`iq4comm.dsp.pulse_shaping`,
:func:`build_eye` folds it into an eye, and the :class:`EyeDiagram` reports the
eye opening, the optimal decision threshold and sampling instant, the Q-factor
(linear and dB), and the BER the eye implies -- tying the shaping choice to a
measurable quality metric and back to BER.

Convention: ``sps`` samples per symbol; a two-symbol eye window is the default.
The one/zero rails are separated by a midpoint threshold (the standard hard
estimate for a binary NRZ eye).
"""

from __future__ import annotations

from dataclasses import dataclass
from math import log10, sqrt

import numpy as np
from scipy.special import erfcinv

from .ber import q_function

__all__ = [
    "q_factor",
    "q_factor_db",
    "q_to_ber",
    "ber_to_q",
    "cluster_binary_levels",
    "EyeDiagram",
    "build_eye",
    "shaped_nrz_waveform",
    "eye_metrics",
]


def q_factor(mu1: float, mu0: float, sigma1: float, sigma0: float) -> float:
    """Q-factor ``(mu1 - mu0) / (sigma1 + sigma0)`` of a two-level signal."""
    denom = sigma1 + sigma0
    if denom <= 0:
        return float("inf")
    return (mu1 - mu0) / denom


def q_factor_db(q: float) -> float:
    """Q-factor in dB, ``20*log10(Q)`` (the optical-comm convention)."""
    if q <= 0:
        return float("-inf")
    return 20.0 * log10(q)


def q_to_ber(q: float) -> float:
    """BER implied by a Q-factor: ``0.5*erfc(Q/sqrt(2)) = Q_function(Q)``."""
    return q_function(q)


def ber_to_q(ber: float) -> float:
    """Q-factor that yields a given BER (inverse of :func:`q_to_ber`)."""
    if not 0.0 < ber < 0.5:
        raise ValueError("ber must be in (0, 0.5)")
    return sqrt(2.0) * erfcinv(2.0 * ber)


def cluster_binary_levels(samples: np.ndarray, *, threshold: float | None = None
                          ) -> tuple[float, float, float, float]:
    """Split samples into low/high rails and return ``(mu0, sigma0, mu1, sigma1)``.

    Uses a midpoint ``threshold`` (defaults to the mean of the sample extremes).
    Empty rails fall back to the overall mean with zero spread.
    """
    s = np.asarray(samples, dtype=float)
    if threshold is None:
        threshold = 0.5 * (s.max() + s.min())
    low = s[s < threshold]
    high = s[s >= threshold]
    mu0 = float(low.mean()) if low.size else float(s.mean())
    mu1 = float(high.mean()) if high.size else float(s.mean())
    sig0 = float(low.std()) if low.size else 0.0
    sig1 = float(high.std()) if high.size else 0.0
    return mu0, sig0, mu1, sig1


@dataclass(frozen=True)
class EyeDiagram:
    """A folded eye diagram and the quality metrics read from it."""

    traces: np.ndarray            # shape (n_traces, window_samples)
    sps: int
    sampling_column: int          # column of maximum vertical opening
    mu0: float
    sigma0: float
    mu1: float
    sigma1: float

    @property
    def eye_amplitude(self) -> float:
        """Level separation ``mu1 - mu0`` (outer eye)."""
        return self.mu1 - self.mu0

    @property
    def eye_height(self) -> float:
        """Inner (noise-margin) opening ``(mu1 - 3 sigma1) - (mu0 + 3 sigma0)``."""
        return (self.mu1 - 3.0 * self.sigma1) - (self.mu0 + 3.0 * self.sigma0)

    @property
    def decision_threshold(self) -> float:
        """Noise-weighted optimal decision level between the rails."""
        if self.sigma0 + self.sigma1 <= 0:
            return 0.5 * (self.mu0 + self.mu1)
        # threshold that equalises the two tail probabilities (sigma-weighted)
        return (self.sigma0 * self.mu1 + self.sigma1 * self.mu0) / (self.sigma0 + self.sigma1)

    @property
    def q_factor(self) -> float:
        return q_factor(self.mu1, self.mu0, self.sigma1, self.sigma0)

    @property
    def q_factor_db(self) -> float:
        return q_factor_db(self.q_factor)

    @property
    def ber(self) -> float:
        """BER implied by the eye's Q-factor."""
        return q_to_ber(self.q_factor)

    @property
    def eye_opening_ratio(self) -> float:
        """Inner opening as a fraction of the outer amplitude (0 = closed)."""
        amp = self.eye_amplitude
        return max(0.0, self.eye_height / amp) if amp > 0 else 0.0


def _best_sampling_column(traces: np.ndarray) -> int:
    """Column with the largest vertical eye opening (min upper - max lower)."""
    best_col, best_open = traces.shape[1] // 2, -np.inf
    for c in range(traces.shape[1]):
        col = traces[:, c]
        thr = 0.5 * (col.max() + col.min())
        low, high = col[col < thr], col[col >= thr]
        if low.size == 0 or high.size == 0:
            continue
        opening = high.min() - low.max()
        if opening > best_open:
            best_open, best_col = opening, c
    return best_col


def build_eye(waveform: np.ndarray, sps: int, *, symbols_per_trace: int = 2,
              offset: int = 0) -> EyeDiagram:
    """Fold a waveform into an eye diagram and compute its quality metrics.

    Splits ``waveform`` into overlapping windows of ``symbols_per_trace`` symbols
    and stacks them; the Q-factor and openings are evaluated at the column of
    maximum vertical opening (the optimal sampling instant).
    """
    if sps < 2:
        raise ValueError("sps must be >= 2")
    w = np.asarray(waveform, dtype=float)[offset:]
    win = symbols_per_trace * sps
    n = w.size // win
    if n < 2:
        raise ValueError("waveform too short for the requested eye window")
    traces = w[: n * win].reshape(n, win)
    col = _best_sampling_column(traces)
    mu0, sig0, mu1, sig1 = cluster_binary_levels(traces[:, col])
    return EyeDiagram(traces, sps, col, mu0, sig0, mu1, sig1)


def shaped_nrz_waveform(bits: np.ndarray, sps: int = 16, *, shape: str = "rc",
                        beta: float = 0.3, span_symbols: int = 8,
                        snr_db: float | None = None, levels: tuple[float, float] = (0.0, 1.0),
                        rng: "np.random.Generator | None" = None) -> np.ndarray:
    """Pulse-shaped, optionally noisy NRZ waveform for eye/Q analysis.

    Maps ``bits`` to ``levels``, upsamples to ``sps`` samples/symbol, and shapes
    with a Nyquist pulse from :mod:`iq4comm.dsp.pulse_shaping` (default raised
    cosine -- the end-to-end matched-RRC response, so the eye is open at the
    sampling instant).  ``snr_db`` (electrical, ``20log10(amplitude/sigma)``) adds
    white Gaussian noise; ``None`` leaves the waveform clean.
    """
    from .pulse_shaping import impulse_response

    b = np.asarray(bits).astype(int)
    lo, hi = levels
    symbols = np.where(b > 0, hi, lo).astype(float)

    up = np.zeros(symbols.size * sps)
    up[::sps] = symbols
    _t, h = impulse_response(shape, beta=beta, span_symbols=span_symbols, sps=sps)
    h = h / h.max()
    wf = np.convolve(up, h, mode="same")

    if snr_db is not None:
        if rng is None:
            rng = np.random.default_rng()
        amp = abs(hi - lo)
        sigma = amp / (10.0 ** (snr_db / 20.0))
        wf = wf + rng.normal(0.0, sigma, wf.shape)
    return wf


def eye_metrics(waveform: np.ndarray, sps: int, **kw) -> EyeDiagram:
    """Convenience wrapper: :func:`build_eye` returning the metrics-bearing eye."""
    return build_eye(waveform, sps, **kw)
