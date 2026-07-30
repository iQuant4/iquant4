"""
Compatibility layer for the former iq4comm quadrature module.

The canonical implementation now lives in iqcore.measurements.
"""

from iqcore.measurements.quadrature import (
    ComplexArray,
    QuadratureStatistics,
    RealArray,
    coherent_quadrature_parameters,
    distribution_statistics,
    expectation_value,
    fock_quadrature_wavefunctions,
    momentum_quadrature_operator,
    position_quadrature_operator,
    quadrature_distribution_normalization,
    quadrature_operator,
    quadrature_probability_density,
    quadrature_statistics,
    sample_quadrature,
)

__all__ = [
    "ComplexArray",
    "QuadratureStatistics",
    "RealArray",
    "coherent_quadrature_parameters",
    "distribution_statistics",
    "expectation_value",
    "fock_quadrature_wavefunctions",
    "momentum_quadrature_operator",
    "position_quadrature_operator",
    "quadrature_distribution_normalization",
    "quadrature_operator",
    "quadrature_probability_density",
    "quadrature_statistics",
    "sample_quadrature",
]
