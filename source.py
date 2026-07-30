"""Compatibility layer for the legacy source module.

New code should import sources from ``iq4comm.sources``.
"""

from iq4comm.sources import BinaryCoherentSource

__all__ = ["BinaryCoherentSource"]
