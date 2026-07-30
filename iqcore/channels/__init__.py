"""Reusable quantum-channel models."""

from .loss import (
    pure_loss_channel,
    pure_loss_kraus_operators,
)

__all__ = [
    "pure_loss_channel",
    "pure_loss_kraus_operators",
]
