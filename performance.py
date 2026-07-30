"""Compatibility layer for the legacy performance module.

New code should import receiver metrics from ``iq4comm.metrics``.
"""

from iq4comm.metrics import ReceiverMetrics

__all__ = ["ReceiverMetrics"]
