"""Pulse shaping and the spectral cost of packing WDM channels.

The modulation *format* sets how many bits ride each symbol; the *pulse shape*
sets how much spectrum each symbol occupies.  Together they decide how tightly
channels can be packed on the ITU grid, and therefore the WDM bandwidth that
feeds the Gaussian-Noise nonlinear-interference term -- so the pulse shape is a
first-class knob on both classical capacity and (through the launch power it
forces) the co-propagating QKD channel.

This module provides the standard family of baseband shaping filters:

* **Root-raised-cosine (RRC)** -- the workhorse.  Split matched-filter pair
  (RRC at the transmitter, RRC at the receiver) whose cascade is a raised-cosine,
  which is Nyquist (zero inter-symbol interference at the symbol instants).
* **Raised-cosine (RC)** -- the full Nyquist pulse; occupied bandwidth
  ``Rs*(1+beta)`` for roll-off ``beta``.
* **Sinc** -- the ``beta -> 0`` brick-wall limit; minimum bandwidth ``Rs`` but
  physically unrealisable and fragile to timing error.
* **Rectangular (NRZ)** -- a time-domain rectangle; trivially causal but a
  ``sinc`` spectrum with slowly-decaying side-lobes, so a wide occupied band.
* **Gaussian** -- smooth, no zero-ISI, set by a time-bandwidth product ``BT``;
  the shape behind GMSK-style formats.

The key figures of merit exposed here are the *occupied bandwidth*, the tightest
*Nyquist channel spacing* a shape allows, and the resulting *spectral
efficiency* ``k / (1 + beta)`` (bits/s/Hz) that ties roll-off directly to the
capacity/coexistence chain.

Conventions: sample rate is ``sps`` samples per symbol; filters are returned on
a symbol-spaced time axis spanning ``+/- span_symbols``.  Bandwidths are the
*occupied* (double-sided baseband) widths in Hz for a given symbol rate ``Rs``.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

__all__ = [
    "PulseShape",
    "rrc_impulse_response",
    "rc_impulse_response",
    "sinc_impulse_response",
    "rect_impulse_response",
    "gaussian_impulse_response",
    "impulse_response",
    "occupied_bandwidth_hz",
    "nyquist_channel_spacing_hz",
    "spectral_efficiency_bits_per_hz",
    "residual_isi",
    "PULSE_SHAPES",
]

PULSE_SHAPES = ("rrc", "rc", "sinc", "rect", "gaussian")


def _time_axis(span_symbols: int, sps: int) -> np.ndarray:
    """Symbol-spaced sample times ``t/Ts`` over ``+/- span_symbols``."""
    if span_symbols < 1:
        raise ValueError("span_symbols must be >= 1")
    if sps < 1:
        raise ValueError("sps must be >= 1")
    n = span_symbols * sps
    return np.arange(-n, n + 1) / sps


def rc_impulse_response(beta: float, span_symbols: int = 10, sps: int = 16
                        ) -> tuple[np.ndarray, np.ndarray]:
    """Raised-cosine impulse response ``h(t/Ts)`` (peak-normalised to 1).

    Returns ``(t_over_Ts, h)``.  ``beta`` in [0, 1] is the roll-off; ``beta=0``
    reduces to a sinc.  The RC pulse is Nyquist: ``h`` has zeros at every nonzero
    integer ``t/Ts``, so a symbol contributes nothing to its neighbours' sample
    instants.
    """
    if not 0.0 <= beta <= 1.0:
        raise ValueError("beta must be in [0, 1]")
    t = _time_axis(span_symbols, sps)
    sinc = np.sinc(t)                                   # sin(pi t)/(pi t)
    denom = 1.0 - (2.0 * beta * t) ** 2
    # cos term, guarding the beta*|2t| = 1 singularities.
    with np.errstate(divide="ignore", invalid="ignore"):
        cos = np.cos(np.pi * beta * t) / denom
    h = sinc * cos
    if beta > 0:
        sing = np.isclose(np.abs(2.0 * beta * t), 1.0)
        if np.any(sing):
            ts = t[sing]
            h[sing] = np.sinc(ts) * (np.pi / 4.0)       # limit of the cos factor
    return t, h


def rrc_impulse_response(beta: float, span_symbols: int = 10, sps: int = 16
                         ) -> tuple[np.ndarray, np.ndarray]:
    """Root-raised-cosine impulse response ``h(t/Ts)`` (peak-normalised to 1).

    The transmit half of the matched pair: ``rrc * rrc`` (convolution) is a
    raised-cosine, so an RRC-at-Tx / RRC-at-Rx link is Nyquist while splitting
    the shaping equally between the two ends (the matched-filter optimum).
    """
    if not 0.0 <= beta <= 1.0:
        raise ValueError("beta must be in [0, 1]")
    t = _time_axis(span_symbols, sps)
    h = np.empty_like(t)
    for i, ti in enumerate(t):
        h[i] = _rrc_point(ti, beta)
    h = h / h.max()
    return t, h


def _rrc_point(t: float, beta: float) -> float:
    """Closed-form RRC value at ``t = t/Ts`` (unnormalised).

    Handles the two removable singularities analytically: ``t=0`` and, for
    ``beta>0``, ``|t| = 1/(4 beta)``.
    """
    if abs(t) < 1e-12:
        return 1.0 - beta + 4.0 * beta / np.pi
    if beta > 0 and abs(abs(t) - 1.0 / (4.0 * beta)) < 1e-9:
        return (beta / np.sqrt(2.0)) * (
            (1.0 + 2.0 / np.pi) * np.sin(np.pi / (4.0 * beta))
            + (1.0 - 2.0 / np.pi) * np.cos(np.pi / (4.0 * beta))
        )
    num = (np.sin(np.pi * t * (1.0 - beta))
           + 4.0 * beta * t * np.cos(np.pi * t * (1.0 + beta)))
    den = np.pi * t * (1.0 - (4.0 * beta * t) ** 2)
    return num / den


def sinc_impulse_response(span_symbols: int = 10, sps: int = 16
                          ) -> tuple[np.ndarray, np.ndarray]:
    """Ideal sinc (brick-wall, ``beta -> 0``) Nyquist pulse, peak-normalised."""
    t = _time_axis(span_symbols, sps)
    return t, np.sinc(t)


def rect_impulse_response(span_symbols: int = 10, sps: int = 16,
                          duty: float = 1.0) -> tuple[np.ndarray, np.ndarray]:
    """Rectangular (NRZ) pulse of width ``duty`` symbols, peak-normalised.

    A time-domain rectangle has a ``sinc`` spectrum with slowly decaying
    side-lobes -- spectrally the least efficient of the family.
    """
    if not 0.0 < duty <= 1.0:
        raise ValueError("duty must be in (0, 1]")
    t = _time_axis(span_symbols, sps)
    h = (np.abs(t) <= duty / 2.0).astype(float)
    return t, h


def gaussian_impulse_response(bt: float, span_symbols: int = 10, sps: int = 16
                              ) -> tuple[np.ndarray, np.ndarray]:
    """Gaussian pulse set by time-bandwidth product ``BT`` (peak-normalised).

    Not a Nyquist pulse -- it has residual ISI -- but bandwidth-compact and
    smooth; ``BT`` around 0.3 is the GMSK/Bluetooth value.  Smaller ``BT`` is
    narrower in frequency but more ISI in time.
    """
    if bt <= 0:
        raise ValueError("bt must be > 0")
    t = _time_axis(span_symbols, sps)
    # Gaussian filter with 3-dB bandwidth B (normalised to Rs) = bt.
    alpha = np.sqrt(np.log(2.0) / 2.0) / bt
    h = np.exp(-(t ** 2) / (2.0 * alpha ** 2))
    return t, h / h.max()


def impulse_response(shape: str, beta: float = 0.2, *, span_symbols: int = 10,
                     sps: int = 16, bt: float = 0.3, duty: float = 1.0
                     ) -> tuple[np.ndarray, np.ndarray]:
    """Dispatch to the named pulse-shape impulse response.

    ``shape`` is one of :data:`PULSE_SHAPES`.  ``beta`` applies to rrc/rc,
    ``bt`` to gaussian, ``duty`` to rect.
    """
    s = shape.lower()
    if s == "rrc":
        return rrc_impulse_response(beta, span_symbols, sps)
    if s == "rc":
        return rc_impulse_response(beta, span_symbols, sps)
    if s == "sinc":
        return sinc_impulse_response(span_symbols, sps)
    if s == "rect":
        return rect_impulse_response(span_symbols, sps, duty)
    if s == "gaussian":
        return gaussian_impulse_response(bt, span_symbols, sps)
    raise ValueError(f"shape must be one of {PULSE_SHAPES}")


def occupied_bandwidth_hz(shape: str, symbol_rate_baud: float, *,
                          beta: float = 0.2, bt: float = 0.3,
                          energy_fraction: float = 0.99, duty: float = 1.0,
                          span_symbols: int = 32, sps: int = 32) -> float:
    """Occupied (double-sided baseband) bandwidth in Hz.

    For the Nyquist shapes this is analytic: sinc gives ``Rs``, RC/RRC give
    ``Rs*(1+beta)``.  For rect/gaussian (no hard band edge) it is the
    ``energy_fraction`` (default 99%) power-containment bandwidth measured from
    the pulse spectrum.
    """
    s = shape.lower()
    rs = symbol_rate_baud
    if s == "sinc":
        return rs
    if s in ("rc", "rrc"):
        if not 0.0 <= beta <= 1.0:
            raise ValueError("beta must be in [0, 1]")
        return rs * (1.0 + beta)
    # Numeric power-containment bandwidth for rect / gaussian.
    _t, h = impulse_response(s, beta=beta, span_symbols=span_symbols, sps=sps,
                             bt=bt, duty=duty)
    return _containment_bandwidth_hz(h, rs, sps, energy_fraction)


def _containment_bandwidth_hz(h: np.ndarray, symbol_rate_baud: float, sps: int,
                              energy_fraction: float) -> float:
    """Double-sided bandwidth (Hz) holding ``energy_fraction`` of spectral power."""
    fs = symbol_rate_baud * sps                        # sample rate
    nfft = 1 << int(np.ceil(np.log2(len(h) * 8)))
    H = np.fft.fftshift(np.fft.fft(h, nfft))
    f = np.fft.fftshift(np.fft.fftfreq(nfft, d=1.0 / fs))
    psd = np.abs(H) ** 2
    total = psd.sum()
    # Grow a symmetric band around DC until it holds the target fraction.
    order = np.argsort(np.abs(f))
    cum = np.cumsum(psd[order]) / total
    idx = np.searchsorted(cum, energy_fraction)
    idx = min(idx, len(order) - 1)
    return 2.0 * float(np.abs(f[order][idx]))


def nyquist_channel_spacing_hz(shape: str, symbol_rate_baud: float, *,
                               beta: float = 0.2, bt: float = 0.3,
                               guard_fraction: float = 0.0, **kw) -> float:
    """Tightest WDM channel spacing (Hz) that avoids linear cross-talk.

    Equals the occupied bandwidth times ``(1 + guard_fraction)``.  For a Nyquist
    shape this is ``Rs*(1+beta)*(1+guard)`` -- the direct link from roll-off to
    how tightly the ITU grid can be filled.
    """
    bw = occupied_bandwidth_hz(shape, symbol_rate_baud, beta=beta, bt=bt, **kw)
    return bw * (1.0 + guard_fraction)


def spectral_efficiency_bits_per_hz(shape: str, bits_per_symbol: float, *,
                                    beta: float = 0.2, bt: float = 0.3,
                                    symbol_rate_baud: float = 1.0, **kw) -> float:
    """Spectral efficiency (bits/s/Hz) = ``k / (occupied_bw / Rs)``.

    For a Nyquist shape this is the familiar ``k / (1 + beta)``: lower roll-off
    packs more bits per hertz, at the cost of a harder-to-build filter.
    """
    bw = occupied_bandwidth_hz(shape, symbol_rate_baud, beta=beta, bt=bt, **kw)
    return bits_per_symbol * symbol_rate_baud / bw


@dataclass(frozen=True)
class PulseShape:
    """A named baseband pulse-shape configuration.

    Bundles a shape and its parameters so the rest of the platform can pass one
    object around (e.g. a channel plan carrying its shaping choice) and read off
    bandwidth / spacing / spectral efficiency without repeating keywords.
    """

    shape: str = "rrc"
    beta: float = 0.2
    bt: float = 0.3
    duty: float = 1.0

    def __post_init__(self) -> None:
        if self.shape.lower() not in PULSE_SHAPES:
            raise ValueError(f"shape must be one of {PULSE_SHAPES}")

    def impulse_response(self, *, span_symbols: int = 10, sps: int = 16
                         ) -> tuple[np.ndarray, np.ndarray]:
        return impulse_response(self.shape, self.beta, span_symbols=span_symbols,
                                sps=sps, bt=self.bt, duty=self.duty)

    def occupied_bandwidth_hz(self, symbol_rate_baud: float, **kw) -> float:
        return occupied_bandwidth_hz(self.shape, symbol_rate_baud, beta=self.beta,
                                     bt=self.bt, duty=self.duty, **kw)

    def channel_spacing_hz(self, symbol_rate_baud: float, *,
                           guard_fraction: float = 0.0, **kw) -> float:
        return nyquist_channel_spacing_hz(self.shape, symbol_rate_baud,
                                          beta=self.beta, bt=self.bt,
                                          guard_fraction=guard_fraction,
                                          duty=self.duty, **kw)

    def spectral_efficiency_bits_per_hz(self, bits_per_symbol: float, *,
                                        symbol_rate_baud: float = 1.0,
                                        **kw) -> float:
        return spectral_efficiency_bits_per_hz(
            self.shape, bits_per_symbol, beta=self.beta, bt=self.bt,
            symbol_rate_baud=symbol_rate_baud, duty=self.duty, **kw)

    def residual_isi(self, **kw) -> float:
        return residual_isi(self.shape, beta=self.beta, bt=self.bt,
                            duty=self.duty, **kw)


def residual_isi(shape: str, *, beta: float = 0.2, bt: float = 0.3,
                 span_symbols: int = 10, sps: int = 16, duty: float = 1.0,
                 matched: bool = True) -> float:
    """Peak residual inter-symbol interference of the end-to-end shape.

    For RRC the end-to-end response is ``rrc * rrc`` (the matched pair) when
    ``matched`` is True; otherwise the single filter is scored.  Returns the
    largest ISI sample magnitude relative to the main tap -- ~0 for a Nyquist
    shape (rrc-matched, rc, sinc) and clearly nonzero for gaussian/rect.
    """
    s = shape.lower()
    if s == "rrc" and matched:
        _t, g = rrc_impulse_response(beta, span_symbols, sps)
        h = np.convolve(g, g)
        h = h / h.max()
        sps_eff = sps
        center = len(h) // 2
    else:
        _t, h = impulse_response(s, beta=beta, span_symbols=span_symbols,
                                 sps=sps, bt=bt, duty=duty)
        h = h / h.max()
        sps_eff = sps
        center = len(h) // 2
    # Sample at nonzero integer symbol offsets and take the worst.
    offsets = np.arange(1, span_symbols) * sps_eff
    taps = [abs(h[center + o]) for o in offsets if center + o < len(h)]
    return max(taps) if taps else 0.0
