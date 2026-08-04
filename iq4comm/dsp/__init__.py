"""Digital signal processing for the iQuant4 communications branch."""

from .ber import (
    q_function,
    ber_theory,
    monte_carlo_ber,
    osnr_db_to_ebn0_db,
    BERPoint,
)
from .gn_model import (
    nli_coefficient,
    nli_power_w,
    effective_snr,
    optimal_launch_power_w,
    ase_power_w,
    gn_operating_point,
    GNOperatingPoint,
)
from .pulse_shaping import (
    PulseShape,
    rrc_impulse_response,
    rc_impulse_response,
    sinc_impulse_response,
    rect_impulse_response,
    gaussian_impulse_response,
    impulse_response,
    occupied_bandwidth_hz,
    nyquist_channel_spacing_hz,
    spectral_efficiency_bits_per_hz,
    residual_isi,
    PULSE_SHAPES,
)

__all__ = [
    "q_function",
    "ber_theory",
    "monte_carlo_ber",
    "osnr_db_to_ebn0_db",
    "BERPoint",
    "nli_coefficient",
    "nli_power_w",
    "effective_snr",
    "optimal_launch_power_w",
    "ase_power_w",
    "gn_operating_point",
    "GNOperatingPoint",
    "PulseShape",
    "rrc_impulse_response",
    "rc_impulse_response",
    "sinc_impulse_response",
    "rect_impulse_response",
    "gaussian_impulse_response",
    "impulse_response",
    "occupied_bandwidth_hz",
    "nyquist_channel_spacing_hz",
    "spectral_efficiency_bits_per_hz",
    "residual_isi",
    "PULSE_SHAPES",
]
