"""Compatibility layer for the legacy homodyne module.

New code should import homodyne receivers from ``iq4comm.receivers``.
"""

from iq4comm.receivers import ErasureHomodyneReceiver, HomodyneReceiver

__all__ = [
    "ErasureHomodyneReceiver",
    "HomodyneReceiver",
]
