from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray


RealVector = NDArray[np.float64]


@dataclass(frozen=True)
class SignFreeOPA:
    """
    Ideal high-gain phase-sensitive OPA measurement.

    In the high-gain limit, measured power is proportional to

        I = G x_phi^2,

    where G = exp(2r). The sign of x_phi is unavailable.
    """

    gain_parameter: float
    phase: float

    def __post_init__(self) -> None:
        if self.gain_parameter < 0.0:
            raise ValueError(
                "OPA gain parameter r cannot be negative."
            )

    @property
    def power_gain(self) -> float:
        """Return G = exp(2r)."""
        return float(
            np.exp(2.0 * self.gain_parameter)
        )

    @property
    def gain_db(self) -> float:
        """Return 10 log10(G)."""
        return float(
            10.0 * np.log10(self.power_gain)
        )

    def measure_power(
        self,
        quadrature_samples: RealVector,
    ) -> RealVector:
        """Return ideal power outcomes I = G x_phi^2."""
        samples = np.asarray(
            quadrature_samples,
            dtype=float,
        )

        return np.asarray(
            self.power_gain * samples**2,
            dtype=np.float64,
        )

    def recover_sign_free_quadrature(
        self,
        power_samples: RealVector,
    ) -> RealVector:
        """Recover |x_phi| from ideal measured power."""
        samples = np.asarray(
            power_samples,
            dtype=float,
        )

        if np.any(samples < 0.0):
            raise ValueError(
                "Power samples cannot be negative."
            )

        return np.asarray(
            np.sqrt(samples / self.power_gain),
            dtype=np.float64,
        )


__all__ = [
    "RealVector",
    "SignFreeOPA",
]
