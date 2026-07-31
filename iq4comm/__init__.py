"""iQuant4Comm: optical and quantum communication tools."""

from ._version import __version__

from .channels import (
    FiberChannel,
    attenuation_db_to_transmissivity,
    fiber_transmissivity,
)
from .metrics import ReceiverMetrics, erasure_pnr_metrics
from .models import ChannelState
from .modulation import (
    Constellation,
    get_constellation,
    modulate,
    demodulate,
)
from .dsp import (
    ber_theory,
    monte_carlo_ber,
    osnr_db_to_ebn0_db,
    q_function,
    BERPoint,
)
from .optimization import OptimizationResult, optimize_receiver
from .receivers import (
    AnalyticalReceiver,
    ErasureHeterodyneReceiver,
    ErasureHomodyneReceiver,
    ErasurePNRReceiver,
    HeterodyneReceiver,
    HomodyneReceiver,
    PNRReceiver,
    Receiver,
)
from .sources import BinaryCoherentSource

__all__ = [
    "__version__",
    "AnalyticalReceiver",
    "BinaryCoherentSource",
    "BERPoint",
    "ChannelState",
    "Constellation",
    "ErasureHeterodyneReceiver",
    "ErasureHomodyneReceiver",
    "ErasurePNRReceiver",
    "FiberChannel",
    "attenuation_db_to_transmissivity",
    "ber_theory",
    "demodulate",
    "fiber_transmissivity",
    "get_constellation",
    "HeterodyneReceiver",
    "HomodyneReceiver",
    "modulate",
    "monte_carlo_ber",
    "osnr_db_to_ebn0_db",
    "OptimizationResult",
    "PNRReceiver",
    "q_function",
    "Receiver",
    "ReceiverMetrics",
    "erasure_pnr_metrics",
    "optimize_receiver",
]
