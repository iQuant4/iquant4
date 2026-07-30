import numpy as np


class BinaryCoherentSource:
    """
    Binary coherent-state source.

    Symbol 0 is transmitted with mean photon number mu_0.
    Symbol 1 is transmitted with mean photon number mu_1.
    """

    def __init__(
        self,
        mu_0: float,
        mu_1: float,
    ) -> None:
        if mu_0 < 0.0 or mu_1 < 0.0:
            raise ValueError(
                "Mean photon numbers cannot be negative."
            )

        if mu_1 <= mu_0:
            raise ValueError(
                "mu_1 must be greater than mu_0."
            )

        self.mu_0 = mu_0
        self.mu_1 = mu_1

    def mean_photon_number(
        self,
        symbol: int,
    ) -> float:
        """
        Return the transmitted mean photon number.
        """

        if symbol == 0:
            return self.mu_0

        if symbol == 1:
            return self.mu_1

        raise ValueError("Symbol must be either 0 or 1.")

    def amplitude(
        self,
        symbol: int,
    ) -> complex:
        """
        Return the coherent-state amplitude alpha.

        For a coherent state:

            mu = |alpha|^2
        """

        mu = self.mean_photon_number(symbol)
        return complex(np.sqrt(mu))

    def __str__(self) -> str:
        return (
            "BinaryCoherentSource("
            f"mu_0={self.mu_0:.3f}, "
            f"mu_1={self.mu_1:.3f}"
            ")"
        )