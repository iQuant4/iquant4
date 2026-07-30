from __future__ import annotations

import numpy as np

from ._types import ComplexVector


def fock_state(
    photon_number: int,
    cutoff: int,
) -> ComplexVector:
    """Create the Fock state |n> in a truncated basis."""
    if photon_number < 0:
        raise ValueError(
            "Photon number cannot be negative."
        )

    if cutoff <= photon_number:
        raise ValueError(
            "Cutoff must be greater than photon number."
        )

    state = np.zeros(
        cutoff,
        dtype=np.complex128,
    )

    state[photon_number] = 1.0

    return state


__all__ = ["fock_state"]
