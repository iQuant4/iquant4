from __future__ import annotations

from typing import TypeAlias

import numpy as np
from numpy.typing import NDArray


ComplexVector: TypeAlias = NDArray[np.complex128]
ComplexMatrix: TypeAlias = NDArray[np.complex128]
QuantumStateArray: TypeAlias = ComplexVector | ComplexMatrix


def as_complex_array(
    state: QuantumStateArray,
) -> NDArray[np.complex128]:
    """Convert a quantum-state input to a complex NumPy array."""
    return np.asarray(
        state,
        dtype=np.complex128,
    )
