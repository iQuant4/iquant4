"""Compatibility layer for the legacy optimizer module.

New code should import receiver optimization from ``iq4comm.optimization``.
"""

from iq4comm.optimization import OptimizationResult, optimize_receiver

__all__ = [
    "OptimizationResult",
    "optimize_receiver",
]
