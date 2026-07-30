"""Communication-channel models and attenuation utilities."""

from .attenuation import (
    attenuation_db_to_transmissivity,
    fiber_transmissivity,
)
from .fiber import FiberChannel

__all__ = [
    "FiberChannel",
    "attenuation_db_to_transmissivity",
    "fiber_transmissivity",
]
