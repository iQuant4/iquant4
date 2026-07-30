"""
Compatibility layer for legacy optical-channel utilities.

New code should import reusable quantum channels from
``iqcore.channels``, phase shifts from ``iqcore.optics``, and
fiber attenuation utilities from ``iq4comm.channels``.
"""

from iq4comm.channels import (
    attenuation_db_to_transmissivity,
    fiber_transmissivity,
)
from iqcore.channels import (
    pure_loss_channel,
    pure_loss_kraus_operators,
)
from iqcore.optics import (
    phase_shift_channel,
    phase_shift_operator,
)

__all__ = [
    "attenuation_db_to_transmissivity",
    "fiber_transmissivity",
    "phase_shift_channel",
    "phase_shift_operator",
    "pure_loss_channel",
    "pure_loss_kraus_operators",
]
