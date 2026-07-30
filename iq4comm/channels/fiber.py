import numpy as np

from iq4comm.channels.attenuation import fiber_transmissivity
from iq4comm.models.channel_state import ChannelState


class FiberChannel:
    """
    Pure-loss optical fiber channel.

    Power transmittance:

        T(d) = 10^(-alpha_db_per_km * d / 10)

    Received mean photon number:

        mu_received = T(d) * mu_transmitted

    Received coherent-state amplitude:

        alpha_received = sqrt(T(d)) * alpha_transmitted
    """

    def __init__(
        self,
        attenuation_db_per_km: float = 0.2,
    ) -> None:
        if attenuation_db_per_km < 0.0:
            raise ValueError(
                "Fiber attenuation cannot be negative."
            )

        self.attenuation_db_per_km = (
            attenuation_db_per_km
        )

    def transmittance(
        self,
        distance_km: float,
    ) -> float:
        if distance_km < 0.0:
            raise ValueError(
                "Distance cannot be negative."
            )

        return fiber_transmissivity(
            distance_km=distance_km,
            loss_db_per_km=(
                self.attenuation_db_per_km
            ),
        )

    def propagate(
        self,
        mu: float,
        alpha: complex,
        distance_km: float,
    ) -> ChannelState:
        """
        Propagate an optical coherent state through the fiber.
        """

        if mu < 0.0:
            raise ValueError(
                "Mean photon number cannot be negative."
            )

        transmission = self.transmittance(
            distance_km
        )

        received_mu = transmission * mu

        received_alpha = (
            np.sqrt(transmission) * alpha
        )

        return ChannelState(
            mu=received_mu,
            alpha=received_alpha,
            distance_km=distance_km,
            transmittance=transmission,
        )

    def __str__(self) -> str:
        return (
            "FiberChannel("
            f"attenuation="
            f"{self.attenuation_db_per_km:.3f} dB/km"
            ")"
        )