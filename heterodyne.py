"""Compatibility layer for the legacy heterodyne module.

New code should import heterodyne receivers from ``iq4comm.receivers``.
"""

from iq4comm.receivers import ErasureHeterodyneReceiver, HeterodyneReceiver

__all__ = [
    "ErasureHeterodyneReceiver",
    "HeterodyneReceiver",
]
