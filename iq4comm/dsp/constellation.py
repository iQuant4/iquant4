"""Constellation diagrams and EVM: the coherent counterpart of the eye.

For on/off-keyed links the eye diagram and Q-factor tell the quality story
(:mod:`iq4comm.dsp.eye`).  For coherent, multi-level formats (QPSK, 16-/64-QAM)
the right instrument is the **constellation diagram** and its scalar summary, the
**error-vector magnitude (EVM)** -- the RMS distance between where each received
symbol landed and where it should have been, normalised to the constellation
power:

    EVM_rms = sqrt( mean|r_i - s_i|^2 / mean|s_i|^2 ).

EVM is the modem-world proxy for SNR: for an AWGN channel with unit-energy
symbols the error power *is* ``1/SNR``, so

    SNR (dB) = -20 log10(EVM_rms) = MER (dB),

the modulation-error-ratio.  From that SNR the closed-form BER follows for any
format, so a few thousand symbols of EVM predict the BER exactly as the eye's
Q-factor does -- but for the formats the eye cannot read.

This module ties to the existing pieces: it builds received constellations with
the real :mod:`iq4comm.modulation` mapper and AWGN, measures EVM/MER, and maps
those to SNR and to :func:`iq4comm.dsp.ber_theory`, so format choice, SNR, EVM,
and BER are one consistent chain.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import log10, sqrt

import numpy as np

from iq4comm.modulation import get_constellation, modulate
from .ber import ber_theory

__all__ = [
    "evm_rms",
    "mer_db",
    "evm_to_snr_db",
    "snr_db_to_evm",
    "evm_to_ber",
    "ConstellationDiagram",
    "received_constellation",
]


def evm_rms(received: np.ndarray, reference: np.ndarray) -> float:
    """RMS error-vector magnitude of ``received`` against ideal ``reference``.

    Normalised to the reference constellation power (data-aided EVM), returned as
    a fraction (multiply by 100 for percent).
    """
    r = np.asarray(received)
    s = np.asarray(reference)
    if r.shape != s.shape:
        raise ValueError("received and reference must have the same shape")
    err_power = np.mean(np.abs(r - s) ** 2)
    ref_power = np.mean(np.abs(s) ** 2)
    if ref_power <= 0:
        return float("inf")
    return float(sqrt(err_power / ref_power))


def mer_db(received: np.ndarray, reference: np.ndarray) -> float:
    """Modulation error ratio (dB) ``= -20 log10(EVM_rms)``."""
    e = evm_rms(received, reference)
    if e <= 0:
        return float("inf")
    return -20.0 * log10(e)


def evm_to_snr_db(evm: float) -> float:
    """Effective SNR (dB) implied by an EVM: ``-20 log10(EVM)``."""
    if evm <= 0:
        return float("inf")
    return -20.0 * log10(evm)


def snr_db_to_evm(snr_db: float) -> float:
    """EVM for a given effective SNR (inverse of :func:`evm_to_snr_db`)."""
    return 10.0 ** (-snr_db / 20.0)


def evm_to_ber(evm: float, fmt: str) -> float:
    """BER predicted from an EVM for format ``fmt`` (via SNR -> Eb/N0 -> theory)."""
    k = get_constellation(fmt).bits_per_symbol
    snr_db = evm_to_snr_db(evm)              # Es/N0
    ebn0_db = snr_db - 10.0 * log10(k)
    return ber_theory(fmt, ebn0_db)


@dataclass(frozen=True)
class ConstellationDiagram:
    """A received constellation and the quality metrics read from it."""

    received: np.ndarray          # complex received symbols
    reference: np.ndarray         # complex ideal (transmitted) symbols
    fmt: str

    @property
    def evm_rms(self) -> float:
        return evm_rms(self.received, self.reference)

    @property
    def evm_percent(self) -> float:
        return 100.0 * self.evm_rms

    @property
    def mer_db(self) -> float:
        return mer_db(self.received, self.reference)

    @property
    def snr_db(self) -> float:
        """Effective Es/N0 (dB) implied by the EVM (equals the MER)."""
        return evm_to_snr_db(self.evm_rms)

    @property
    def ber(self) -> float:
        """BER predicted from the measured EVM."""
        return evm_to_ber(self.evm_rms, self.fmt)


def received_constellation(fmt: str, snr_db: float, *, n_symbols: int = 4000,
                           rng: "np.random.Generator | None" = None
                           ) -> ConstellationDiagram:
    """Simulate a received constellation at a given Es/N0 (dB).

    Maps random bits through the real :mod:`iq4comm.modulation` constellation
    (unit average energy) and adds complex AWGN of variance ``1/SNR`` split over
    I and Q, so the measured EVM recovers the set SNR.
    """
    if rng is None:
        rng = np.random.default_rng()
    const = get_constellation(fmt)
    k = const.bits_per_symbol
    bits = rng.integers(0, 2, size=n_symbols * k)
    tx = modulate(bits, const)
    esn0 = 10.0 ** (snr_db / 10.0)
    noise_var = 1.0 / esn0
    noise = sqrt(noise_var / 2.0) * (
        rng.standard_normal(tx.shape) + 1j * rng.standard_normal(tx.shape))
    rx = tx + noise
    return ConstellationDiagram(rx, tx, fmt)
