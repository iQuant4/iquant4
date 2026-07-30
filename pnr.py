"""Compatibility layer for the legacy PNR module.

New code should import PNR receivers from ``iq4comm.receivers``.
"""

from iq4comm.receivers import ErasurePNRReceiver, PNRReceiver

__all__ = [
    "ErasurePNRReceiver",
    "PNRReceiver",
]
