"""Digital modulation formats for the iQuant4 communications branch.

Gray-coded constellations for the standard coherent-optics formats -- BPSK,
QPSK, 16-QAM, 64-QAM -- plus intensity OOK.  Each :class:`Constellation` is
normalised to unit average symbol energy and carries a Gray bit-map, so
nearest-neighbour symbol errors cost a single bit (the assumption behind the
closed-form BER formulas in :mod:`iq4comm.dsp.ber`).
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

__all__ = [
    "Constellation",
    "get_constellation",
    "modulate",
    "demodulate",
    "FORMATS",
]


def _gray(n: int) -> int:
    """Binary-reflected Gray code of ``n``."""
    return n ^ (n >> 1)


def _int_to_bits(value: int, width: int) -> list[int]:
    return [(value >> (width - 1 - i)) & 1 for i in range(width)]


def _pam_levels(bits_per_axis: int) -> np.ndarray:
    """Odd-integer PAM amplitudes: -(L-1), ..., -1, +1, ..., +(L-1)."""
    length = 2 ** bits_per_axis
    return np.array([2 * p - (length - 1) for p in range(length)], dtype=float)


@dataclass(frozen=True)
class Constellation:
    """A normalised, Gray-coded constellation.

    Attributes
    ----------
    name:
        Format label (e.g. ``"16QAM"``).
    bits_per_symbol:
        ``k = log2(M)``.
    points:
        Complex symbol positions, length ``M``, unit average energy.
    symbol_bits:
        ``(M, k)`` array of 0/1; row ``s`` is the bit label of ``points[s]``.
    """

    name: str
    bits_per_symbol: int
    points: np.ndarray
    symbol_bits: np.ndarray

    @property
    def order(self) -> int:
        return len(self.points)

    @property
    def _lut(self) -> np.ndarray:
        """Map integer bit-label -> point (for fast modulation)."""
        lut = np.zeros(self.order, dtype=np.complex128)
        for s in range(self.order):
            value = 0
            for b in self.symbol_bits[s]:
                value = (value << 1) | int(b)
            lut[value] = self.points[s]
        return lut


def _build_square_qam(name: str, order: int) -> Constellation:
    k = int(round(np.log2(order)))
    if 2 ** k != order or k % 2 != 0:
        raise ValueError(f"{name}: order must be a square power of two")
    k_axis = k // 2
    amps = _pam_levels(k_axis)
    length = len(amps)

    points = []
    bits = []
    for p_i in range(length):
        for p_q in range(length):
            points.append(amps[p_i] + 1j * amps[p_q])
            label = _int_to_bits(_gray(p_i), k_axis) + _int_to_bits(_gray(p_q), k_axis)
            bits.append(label)
    pts = np.array(points, dtype=np.complex128)
    pts /= np.sqrt(np.mean(np.abs(pts) ** 2))
    return Constellation(name, k, pts, np.array(bits, dtype=int))


def _build_bpsk() -> Constellation:
    pts = np.array([-1.0 + 0j, 1.0 + 0j])
    bits = np.array([[0], [1]], dtype=int)  # Gray-trivial
    return Constellation("BPSK", 1, pts, bits)


def _build_ook() -> Constellation:
    # Intensity levels 0 and A with unit average energy: A^2/2 = 1.
    a = np.sqrt(2.0)
    pts = np.array([0.0 + 0j, a + 0j])
    bits = np.array([[0], [1]], dtype=int)
    return Constellation("OOK", 1, pts, bits)


FORMATS = {
    "OOK": _build_ook,
    "BPSK": _build_bpsk,
    "QPSK": lambda: _build_square_qam("QPSK", 4),
    "16QAM": lambda: _build_square_qam("16QAM", 16),
    "64QAM": lambda: _build_square_qam("64QAM", 64),
}


def get_constellation(name: str) -> Constellation:
    key = name.upper().replace("-", "").replace("_", "")
    if key not in FORMATS:
        raise ValueError(f"unknown format {name!r}; choose from {sorted(FORMATS)}")
    return FORMATS[key]()


def modulate(bits: np.ndarray, constellation: Constellation) -> np.ndarray:
    """Map a bit stream to complex symbols (MSB-first within each symbol)."""
    bits = np.asarray(bits, dtype=int).ravel()
    k = constellation.bits_per_symbol
    if bits.size % k != 0:
        raise ValueError(f"bit count {bits.size} not a multiple of {k}")
    groups = bits.reshape(-1, k)
    weights = (1 << np.arange(k - 1, -1, -1))
    values = groups @ weights
    return constellation._lut[values]


def demodulate(symbols: np.ndarray, constellation: Constellation) -> np.ndarray:
    """Hard-decision nearest-neighbour demapping back to bits."""
    symbols = np.asarray(symbols, dtype=np.complex128).ravel()
    # nearest constellation point for each symbol
    dist = np.abs(symbols[:, None] - constellation.points[None, :])
    nearest = np.argmin(dist, axis=1)
    return constellation.symbol_bits[nearest].ravel()
