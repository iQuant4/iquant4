"""
Compatibility layer for legacy pure-state quadrature sampling.

New code should import these helpers from
``iqcore.measurements.homodyne_sampling``.
"""

from iqcore.measurements.homodyne_sampling import (
    RealVector,
    quadrature_probability_density,
    quadrature_wavefunction,
    sample_from_density,
    sign_free_samples,
)
from iqcore.states import ComplexVector

__all__ = [
    "ComplexVector",
    "RealVector",
    "quadrature_probability_density",
    "quadrature_wavefunction",
    "sample_from_density",
    "sign_free_samples",
]
