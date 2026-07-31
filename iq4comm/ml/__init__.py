"""Machine-learning layer for the iQuant4 communications branch.

Learned nonlinearity compensation trained on data from the platform's own fiber
models.  Uses numpy/scikit-learn (no autodiff dependency) so it runs anywhere
the rest of iQuant4 does.
"""

from .dataset import kerr_phase_channel, make_dataset, Dataset
from .equalizers import (
    LinearEqualizer,
    VolterraEqualizer,
    NeuralEqualizer,
    evm,
    symbol_ber,
)

__all__ = [
    "kerr_phase_channel",
    "make_dataset",
    "Dataset",
    "LinearEqualizer",
    "VolterraEqualizer",
    "NeuralEqualizer",
    "evm",
    "symbol_ber",
]
