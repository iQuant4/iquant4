"""iQuant4Comm: optical and quantum communication tools."""

from ._version import __version__

from .channels import (
    FiberChannel,
    attenuation_db_to_transmissivity,
    fiber_transmissivity,
)
from .metrics import ReceiverMetrics, erasure_pnr_metrics
from .models import ChannelState
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
    "ChannelState",
    "ErasureHeterodyneReceiver",
    "ErasureHomodyneReceiver",
    "ErasurePNRReceiver",
    "FiberChannel",
    "attenuation_db_to_transmissivity",
    "fiber_transmissivity",
    "HeterodyneReceiver",
    "HomodyneReceiver",
    "OptimizationResult",
    "PNRReceiver",
    "Receiver",
    "ReceiverMetrics",
    "erasure_pnr_metrics",
    "optimize_receiver",
]
