"""Bridge the shared ``FiberSpec`` to the quantum pure-loss channel.

This module is the concrete expression of the platform's shared-foundation
rule: the same :class:`iqcore.fiber.FiberSpec` that the classical branch
propagates optical fields through also drives the quantum bosonic pure-loss
channel, through the span's power transmissivity.  Define a fiber span once and
both branches see identical loss.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from .loss import pure_loss_channel

if TYPE_CHECKING:  # pragma: no cover - typing only
    from iqcore.fiber import FiberSpec
    from iqcore.states import ComplexMatrix, QuantumStateArray

__all__ = ["fiber_loss_channel"]


def fiber_loss_channel(
    state: "QuantumStateArray",
    fiber: "FiberSpec",
    length_km: float,
) -> "ComplexMatrix":
    """Apply the bosonic pure-loss channel of a physical fiber span.

    Parameters
    ----------
    state:
        Input single-mode quantum state (truncated Fock representation).
    fiber:
        A :class:`iqcore.fiber.FiberSpec`; its attenuation sets the span loss.
    length_km:
        Span length in kilometres.

    Returns
    -------
    ComplexMatrix
        The output density matrix after propagation through ``length_km`` of
        ``fiber``, computed with the existing :func:`pure_loss_channel` and the
        span transmissivity ``eta = fiber.transmissivity(length_km)``.
    """
    eta = fiber.transmissivity(length_km)
    return pure_loss_channel(state, eta)
