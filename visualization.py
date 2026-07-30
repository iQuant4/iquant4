"""
Compatibility layer for the legacy visualization module.

Numerical photon statistics now live in :mod:`iqcore.metrics`,
and plotting helpers live in :mod:`iqcore.visualization`.
"""

from iqcore.metrics import (
    mean_photon_number,
    photon_number_distribution,
    photon_number_variance,
    state_purity,
)
from iqcore.visualization import (
    plot_density_matrix,
    plot_fock_distribution,
    plot_state_summary,
    print_state_summary,
)

__all__ = [
    "mean_photon_number",
    "photon_number_distribution",
    "photon_number_variance",
    "plot_density_matrix",
    "plot_fock_distribution",
    "plot_state_summary",
    "print_state_summary",
    "state_purity",
]
