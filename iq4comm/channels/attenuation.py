from __future__ import annotations


def attenuation_db_to_transmissivity(
    attenuation_db: float,
) -> float:
    """Convert nonnegative power attenuation in dB to transmissivity."""
    if attenuation_db < 0.0:
        raise ValueError(
            "Attenuation cannot be negative."
        )

    return float(
        10.0 ** (-attenuation_db / 10.0)
    )


def fiber_transmissivity(
    distance_km: float,
    loss_db_per_km: float = 0.2,
) -> float:
    """Calculate fiber power transmissivity."""
    if distance_km < 0.0:
        raise ValueError(
            "Distance cannot be negative."
        )

    if loss_db_per_km < 0.0:
        raise ValueError(
            "Fiber loss cannot be negative."
        )

    return attenuation_db_to_transmissivity(
        attenuation_db=(
            loss_db_per_km * distance_km
        )
    )


__all__ = [
    "attenuation_db_to_transmissivity",
    "fiber_transmissivity",
]
