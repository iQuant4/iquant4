"""Compatibility layer for the legacy metrics module.

New code should import metrics from ``iq4comm.metrics``.
"""

from iq4comm.metrics import erasure_pnr_metrics

__all__ = ["erasure_pnr_metrics"]
