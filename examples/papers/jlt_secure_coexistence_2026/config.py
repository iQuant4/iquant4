"""Frozen reference configuration for the JLT secure-coexistence paper.

Every figure and headline number in the manuscript is generated from this
single configuration. Changing a value here changes all downstream outputs.
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class RefConfig:
    L_km: float = 80.0
    n_channels: int = 8
    spacing_hz: float = 50e9
    symbol_rate_baud: float = 32e9        # classical R_s
    noise_figure_db: float = 5.0
    r_min: float = 1e-6                    # bits/use security floor
    # quantum
    quantum_cband_nm: float = 1546.12
    classical_center_nm: float = 1550.0
    quantum_oband_nm: float = 1310.0
    oband_attenuation_db_per_km: float = 0.32
    # CV detector
    cv_efficiency: float = 0.6
    cv_electronic_noise: float = 0.05
    cv_reconciliation: float = 0.95
    modulation_variance: float = 4.0


CONFIG = RefConfig()
