"""Bit-error-rate: closed-form theory, Monte-Carlo simulation, and the
OSNR -> SNR -> Eb/N0 bridge that ties BER back to the fiber link.

Theory (Gray-coded, AWGN)
-------------------------
* BPSK / QPSK:  ``BER = Q(sqrt(2 * Eb/N0))``
* Square M-QAM: nearest-neighbour approximation
  ``BER ~= 4/k (1 - 1/sqrt(M)) Q( sqrt(3k/(M-1) * Eb/N0) )``, ``k = log2(M)``
* OOK (coherent, optimal threshold): ``BER = Q(sqrt(Eb/N0))``

The Monte-Carlo path pushes random bits through the real
:mod:`iq4comm.modulation` mapper and AWGN, and agrees with these formulas --
that agreement is the module's test.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import erfc, log2, sqrt

import numpy as np

from iq4comm.modulation import get_constellation, modulate, demodulate

__all__ = [
    "q_function",
    "ber_theory",
    "monte_carlo_ber",
    "osnr_db_to_ebn0_db",
    "BERPoint",
]


def q_function(x: float) -> float:
    """Gaussian tail ``Q(x) = 0.5 * erfc(x / sqrt(2))``."""
    return 0.5 * erfc(x / sqrt(2.0))


def _ebn0_linear(ebn0_db: float) -> float:
    return 10.0 ** (ebn0_db / 10.0)


def ber_theory(fmt: str, ebn0_db: float) -> float:
    """Closed-form AWGN BER for a Gray-coded format at a given Eb/N0 (dB)."""
    key = fmt.upper().replace("-", "").replace("_", "")
    ebn0 = _ebn0_linear(ebn0_db)
    if key in ("BPSK", "QPSK"):
        return q_function(sqrt(2.0 * ebn0))
    if key == "OOK":
        return q_function(sqrt(ebn0))
    if key.endswith("QAM"):
        const = get_constellation(key)
        m = const.order
        k = const.bits_per_symbol
        coeff = (4.0 / k) * (1.0 - 1.0 / sqrt(m))
        return coeff * q_function(sqrt(3.0 * k / (m - 1) * ebn0))
    raise ValueError(f"no theory for format {fmt!r}")


@dataclass(frozen=True)
class BERPoint:
    ebn0_db: float
    ber: float
    bit_errors: int
    bits: int


def monte_carlo_ber(fmt: str, ebn0_db: float, *, num_bits: int = 1_000_000,
                    rng: "np.random.Generator | None" = None) -> BERPoint:
    """Simulated BER: random bits -> symbols -> AWGN -> hard decision.

    Noise is added at complex-symbol level with total variance ``N0 = 1/(Es/N0)``
    (unit average symbol energy), split evenly across the I and Q rails.
    """
    if rng is None:
        rng = np.random.default_rng()
    const = get_constellation(fmt)
    k = const.bits_per_symbol
    num_bits -= num_bits % k
    bits = rng.integers(0, 2, size=num_bits)
    symbols = modulate(bits, const)

    esn0 = _ebn0_linear(ebn0_db) * k           # Es/N0 = k * Eb/N0
    noise_var_total = 1.0 / esn0               # unit average energy
    noise = sqrt(noise_var_total / 2.0) * (
        rng.standard_normal(symbols.shape) + 1j * rng.standard_normal(symbols.shape))
    received = symbols + noise

    decided = demodulate(received, const)
    bit_errors = int(np.count_nonzero(decided != bits))
    return BERPoint(ebn0_db, bit_errors / num_bits, bit_errors, num_bits)


def osnr_db_to_ebn0_db(osnr_db: float, symbol_rate_baud: float, *,
                       bits_per_symbol: int,
                       reference_bandwidth_hz: float = 12.5e9,
                       polarizations: int = 2) -> float:
    """Convert optical OSNR (dB) to Eb/N0 (dB).

    ``SNR = OSNR * (polarizations * B_ref) / R_s`` (electrical SNR after a matched
    filter of noise bandwidth ``R_s``), then ``Eb/N0 = SNR / log2(M)``.  This is
    the bridge from a :class:`iqcore.fiber.Link` OSNR to a modulation BER.
    """
    osnr_lin = 10.0 ** (osnr_db / 10.0)
    snr_lin = osnr_lin * (polarizations * reference_bandwidth_hz) / symbol_rate_baud
    ebn0_lin = snr_lin / bits_per_symbol
    return 10.0 * np.log10(ebn0_lin)
