"""Finite-block sensitivity corrections for QKD.

Asymptotic key rates assume an infinite number of exchanged signals.  Real
systems process a finite block of ``N`` pulses, and composable security then
costs two things: statistical fluctuations inflate the estimated error rate
(you cannot know the true QBER from a finite sample), and privacy amplification
/ error verification carry finite overhead terms that vanish only as ``1/N``.

This module provides a compact, self-contained finite-key secret-fraction model
that captures the essential behaviour: the rate converges to the asymptotic
value as ``N -> infinity``, is strictly lower for finite ``N``, and drops to
zero below a minimum block size (and hence shortens reach).  It is a simplified
Hoeffding-bound model, not a full tight finite-key proof.

Reference (framework): Lim et al., "Concise security bounds for practical
decoy-state QKD," Phys. Rev. A 89, 022307 (2014); Tomamichel et al., Nat.
Commun. 3, 634 (2012).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from math import log, log2, sqrt

from .model_status import FINITE_KEY_MODEL, ModelStatus

__all__ = ["FiniteKeyParams", "finite_key_fraction", "FINITE_KEY_MODEL"]


def _h2(x: float) -> float:
    if x <= 0.0 or x >= 1.0:
        return 0.0
    return -x * log2(x) - (1.0 - x) * log2(1.0 - x)


@dataclass(frozen=True)
class FiniteKeyParams:
    """Finite-key regime parameters.

    Attributes
    ----------
    block_size:
        Number of transmitted signals ``N`` in the key session.
    eps_security:
        Composable security parameter (e.g. 1e-9).
    """

    block_size: float = 1e10
    eps_security: float = 1e-9
    model_status: ModelStatus = field(
        default=ModelStatus.SENSITIVITY_ESTIMATE, init=False)

    def __post_init__(self) -> None:
        if self.block_size <= 0:
            raise ValueError("block_size must be positive")
        if not 0.0 < self.eps_security < 1.0:
            raise ValueError("eps_security must lie in (0, 1)")


def finite_key_fraction(gain: float, error: float, *,
                        error_correction_eff: float = 1.16,
                        sift: float = 0.5,
                        params: "FiniteKeyParams | None" = None) -> float:
    """Secret-fraction sensitivity estimate (bits/pulse) from gain and QBER.

    With ``params=None`` this is the asymptotic fraction
    ``sift * gain * [1 - (1+f) H2(e)]``.  With finite ``params`` it applies a
    generic Hoeffding fluctuation ``t = sqrt(ln(1/eps) / (2 n))`` to the error estimate
    (``n`` = detected sifted events) and subtracts the ``O(1/N)`` composable
    privacy-amplification / error-verification terms.  The result has model
    status ``sensitivity_estimate`` and is not a protocol-specific composable
    security proof.
    """
    if gain <= 0.0:
        return 0.0
    e = min(max(error, 0.0), 0.5)
    f = error_correction_eff
    if params is None:
        return max(sift * gain * (1.0 - (1.0 + f) * _h2(e)), 0.0)

    n = sift * gain * params.block_size
    if n < 1.0:
        return 0.0
    eps = params.eps_security
    t = sqrt(log(1.0 / eps) / (2.0 * n))            # error-estimate fluctuation
    e_ub = min(e + t, 0.5)
    finite_terms = (6.0 * log2(21.0 / eps) + log2(2.0 / eps)) / params.block_size
    return max(sift * gain * (1.0 - _h2(e_ub))
               - sift * gain * f * _h2(e) - finite_terms, 0.0)
