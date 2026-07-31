"""Training-data generation for ML-based nonlinearity compensation.

Symbols are pushed through a reduced fiber-Kerr channel -- an intensity-dependent
phase rotation (self-phase modulation) plus AWGN::

    rx = tx * exp(i * phi_nl * |tx|^2) + n

A *linear* equaliser cannot undo the intensity-dependent phase (it is not a
linear function of ``tx``); a learned equaliser can.  This is the compact,
dependency-light channel used to demonstrate the ML layer.  The full waveform
NLSE solver in :mod:`iqcore.fiber` can also generate data for higher-fidelity
studies.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from iq4comm.modulation import get_constellation, modulate

__all__ = ["kerr_phase_channel", "make_dataset", "Dataset"]


@dataclass
class Dataset:
    tx: np.ndarray          # transmitted symbols (complex)
    rx: np.ndarray          # received symbols (complex)
    bits: np.ndarray        # transmitted bits
    fmt: str                # modulation format

    def split(self, train_frac: float = 0.7):
        n = int(len(self.tx) * train_frac)
        k = get_constellation(self.fmt).bits_per_symbol
        train = Dataset(self.tx[:n], self.rx[:n], self.bits[:n * k], self.fmt)
        test = Dataset(self.tx[n:], self.rx[n:], self.bits[n * k:], self.fmt)
        return train, test


def kerr_phase_channel(tx: np.ndarray, phi_nl: float, snr_db: float,
                       rng: np.random.Generator) -> np.ndarray:
    """Apply intensity-dependent phase rotation (SPM) and AWGN to symbols."""
    rotated = tx * np.exp(1j * phi_nl * np.abs(tx) ** 2)
    es = float(np.mean(np.abs(tx) ** 2))
    n0 = es / (10.0 ** (snr_db / 10.0))
    noise = np.sqrt(n0 / 2.0) * (rng.standard_normal(rotated.shape)
                                 + 1j * rng.standard_normal(rotated.shape))
    return rotated + noise


def make_dataset(fmt: str, n_symbols: int, *, phi_nl: float = 0.15,
                 snr_db: float = 20.0, seed: int = 0) -> Dataset:
    """Generate a (tx, rx, bits) dataset over the Kerr phase channel."""
    rng = np.random.default_rng(seed)
    const = get_constellation(fmt)
    bits = rng.integers(0, 2, size=n_symbols * const.bits_per_symbol)
    tx = modulate(bits, const)
    rx = kerr_phase_channel(tx, phi_nl, snr_db, rng)
    return Dataset(tx=tx, rx=rx, bits=bits, fmt=fmt)
