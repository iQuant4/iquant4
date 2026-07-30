"""Compatibility layer for the legacy channel module.

New code should import channels from ``iq4comm.channels``.
"""

from iq4comm.channels import FiberChannel

__all__ = ["FiberChannel"]
