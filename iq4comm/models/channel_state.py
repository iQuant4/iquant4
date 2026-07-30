from dataclasses import dataclass


@dataclass(frozen=True)
class ChannelState:
    """
    Optical state delivered by the channel to a receiver.
    """

    mu: float
    alpha: complex
    distance_km: float
    transmittance: float

    def __post_init__(self) -> None:
        if self.mu < 0.0:
            raise ValueError("Mean photon number cannot be negative.")

        if self.distance_km < 0.0:
            raise ValueError("Distance cannot be negative.")

        if not 0.0 <= self.transmittance <= 1.0:
            raise ValueError(
                "Transmittance must be between 0 and 1."
            )