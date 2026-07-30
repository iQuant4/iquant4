"""Compatibility layer for the legacy state module.

New code should import :class:`ChannelState` from ``iq4comm.models``.
"""

from iq4comm.models import ChannelState

__all__ = ["ChannelState"]
