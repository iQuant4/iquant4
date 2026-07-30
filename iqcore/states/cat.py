from __future__ import annotations

import numpy as np

from ._types import ComplexVector
from .coherent import coherent_state


def even_cat_state(
    alpha: complex,
    cutoff: int,
) -> ComplexVector:
    """
    Create the normalized even cat state

        |cat+> ∝ |alpha> + |-alpha>.
    """
    positive_state = coherent_state(
        alpha=alpha,
        cutoff=cutoff,
    )

    negative_state = coherent_state(
        alpha=-alpha,
        cutoff=cutoff,
    )

    state = positive_state + negative_state

    norm = np.linalg.norm(state)

    if norm == 0.0:
        raise ValueError(
            "Even cat-state normalization is zero."
        )

    return state / norm


def odd_cat_state(
    alpha: complex,
    cutoff: int,
) -> ComplexVector:
    """
    Create the normalized odd cat state

        |cat-> ∝ |alpha> - |-alpha>.
    """
    positive_state = coherent_state(
        alpha=alpha,
        cutoff=cutoff,
    )

    negative_state = coherent_state(
        alpha=-alpha,
        cutoff=cutoff,
    )

    state = positive_state - negative_state

    norm = np.linalg.norm(state)

    if norm == 0.0:
        raise ValueError(
            "Odd cat-state normalization is zero."
        )

    return state / norm


__all__ = [
    "even_cat_state",
    "odd_cat_state",
]
