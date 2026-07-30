"""Compatibility layer for the legacy receiver module.

New code should import receiver bases from ``iq4comm.receivers``.
"""

from iq4comm.receivers import AnalyticalReceiver, Receiver

__all__ = [
    "AnalyticalReceiver",
    "Receiver",
]
