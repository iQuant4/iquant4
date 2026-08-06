"""Quantum key distribution for the iQuant4 platform.

Key-rate models that sit directly on the shared fiber foundation: the same
:class:`iqcore.fiber.FiberSpec` transmissivity that drives the classical link
also parametrises the QKD secret-key rate, so classical and quantum performance
are computed from one physical description of the fiber -- including their
coexistence coupling (:mod:`iq4comm.qkd.coexistence`).
"""

from .dv import (
    binary_entropy,
    plob_bound_bits,
    DetectorModel,
    bb84_decoy_key_rate,
    bb84_rate_vs_distance,
)
from .cv import (
    holevo_g,
    CVDetector,
    cvqkd_homodyne_key_rate,
    cvqkd_rate_vs_distance,
)
from .coexistence import (
    RamanModel,
    raman_background_yield,
    raman_photon_occupation,
    cv_raman_excess_noise,
    coexistence_dv_key_rate,
    coexistence_cv_key_rate,
    classical_capacity_bps,
    coexistence_curve,
    CoexistencePoint,
)
from .raman_spectrum import (
    silica_raman_gain,
    phonon_occupation,
    spontaneous_raman_efficiency,
    band_raman_coefficient,
    resolved_raman_rho_effective,
    ClassicalChannel,
)
from .multispan import (
    multispan_classical_capacity_bps,
    multispan_raman_background_yield,
    multispan_raman_photon_occupation,
    multispan_dv_key_rate,
    multispan_cv_key_rate,
)
from .entanglement import (
    PairSource,
    heralded_g2,
    source_fidelity,
    coincidence_rate,
    coincidence_qber,
    elementary_link_fidelity,
    bbm92_key_rate,
    entanglement_reach_km,
    EntanglementLink,
    evaluate_link,
)
from .finite_key import (
    FiniteKeyParams,
    finite_key_fraction,
)
from .optimize import (
    OperatingPoint,
    optimize_launch_power,
    coexistence_reach,
    protocol_coexistence_key_rate,
    select_best_protocol,
)
from .protocols import (
    mdi_qkd_key_rate,
    tf_qkd_key_rate,
    trusted_node_key_rate,
)
from .format_impact import (
    channel_snr_db,
    format_ber,
    format_capacity_bps,
    minimum_launch_for_format_dbm,
    FormatImpact,
    format_qkd_tradeoff,
)
from .spectral_design import (
    channels_in_band,
    GridFillPoint,
    grid_fill_tradeoff,
    best_rolloff_for_key_rate,
)
from .system_model import (
    roadm_insertion_loss_db,
    system_key_rate,
    SystemPoint,
    system_operating_point,
)
from .repeater import (
    fidelity_to_p,
    p_to_fidelity,
    swap_fidelity,
    chained_fidelity,
    werner_qber,
    entanglement_key_fraction,
    direct_plob_rate,
    repeater_secret_key_rate,
    optimal_segment_count,
    repeater_advantage_distance,
    RepeaterLink,
)

__all__ = [
    "binary_entropy",
    "plob_bound_bits",
    "DetectorModel",
    "bb84_decoy_key_rate",
    "bb84_rate_vs_distance",
    "holevo_g",
    "CVDetector",
    "cvqkd_homodyne_key_rate",
    "cvqkd_rate_vs_distance",
    "RamanModel",
    "raman_background_yield",
    "raman_photon_occupation",
    "cv_raman_excess_noise",
    "coexistence_dv_key_rate",
    "coexistence_cv_key_rate",
    "classical_capacity_bps",
    "coexistence_curve",
    "CoexistencePoint",
    "silica_raman_gain",
    "phonon_occupation",
    "spontaneous_raman_efficiency",
    "band_raman_coefficient",
    "resolved_raman_rho_effective",
    "ClassicalChannel",
    "multispan_classical_capacity_bps",
    "multispan_raman_background_yield",
    "multispan_raman_photon_occupation",
    "multispan_dv_key_rate",
    "multispan_cv_key_rate",
    "PairSource",
    "heralded_g2",
    "source_fidelity",
    "coincidence_rate",
    "coincidence_qber",
    "elementary_link_fidelity",
    "bbm92_key_rate",
    "entanglement_reach_km",
    "EntanglementLink",
    "evaluate_link",
    "OperatingPoint",
    "optimize_launch_power",
    "coexistence_reach",
    "protocol_coexistence_key_rate",
    "select_best_protocol",
    "FiniteKeyParams",
    "finite_key_fraction",
    "mdi_qkd_key_rate",
    "tf_qkd_key_rate",
    "trusted_node_key_rate",
    "channel_snr_db",
    "format_ber",
    "format_capacity_bps",
    "minimum_launch_for_format_dbm",
    "FormatImpact",
    "format_qkd_tradeoff",
    "channels_in_band",
    "GridFillPoint",
    "grid_fill_tradeoff",
    "best_rolloff_for_key_rate",
    "roadm_insertion_loss_db",
    "system_key_rate",
    "SystemPoint",
    "system_operating_point",
    "fidelity_to_p",
    "p_to_fidelity",
    "swap_fidelity",
    "chained_fidelity",
    "werner_qber",
    "entanglement_key_fraction",
    "direct_plob_rate",
    "repeater_secret_key_rate",
    "optimal_segment_count",
    "repeater_advantage_distance",
    "RepeaterLink",
]
