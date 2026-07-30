from __future__ import annotations

from typing import TYPE_CHECKING, Optional

import numpy as np

from iq4comm.channels.attenuation import fiber_transmissivity
from iq4comm.models.channel_state import ChannelState

if TYPE_CHECKING:  # pragma: no cover - typing only
    from iqcore.fiber import FiberSpec


class FiberChannel:
    """
    Pure-loss optical fiber channel.

    Power transmittance:

        T(d) = 10^(-alpha_db_per_km * d / 10)

    Received mean photon number:

        mu_received = T(d) * mu_transmitted

    Received coherent-state amplitude:

        alpha_received = sqrt(T(d)) * alpha_transmitted

    A channel may also be built from a shared :class:`iqcore.fiber.FiberSpec`
    via :meth:`from_spec`, so the communications branch and the ``iqcore``
    engine describe a span with one object.  When constructed that way the spec
    is retained on :attr:`spec` for downstream field-level propagation with
    :func:`iqcore.fiber.propagate`.
    """

    def __init__(
        self,
        attenuation_db_per_km: float = 0.2,
        spec: "Optional[FiberSpec]" = None,
    ) -> None:
        if attenuation_db_per_km < 0.0:
            raise ValueError(
                "Fiber attenuation cannot be negative."
            )

        self.attenuation_db_per_km = (
            attenuation_db_per_km
        )
        self.spec = spec

    @classmethod
    def from_spec(cls, spec: "FiberSpec") -> "FiberChannel":
        """Build a :class:`FiberChannel` from a shared ``iqcore`` FiberSpec.

        The channel's attenuation is taken from ``spec.attenuation_db_per_km``
        so the comm branch and ``iqcore`` share a single fiber description; the
        spec itself is stored on :attr:`spec`.
        """
        return cls(
            attenuation_db_per_km=spec.attenuation_db_per_km,
            spec=spec,
        )

    def transmittance(
        self,
        distance_km: float,
    ) -> float:
        if distance_km < 0.0:
            raise ValueError(
                "Distance cannot be negative."
            )

        return fiber_transmissivity(
            distance_km=distance_km,
            loss_db_per_km=(
                self.attenuation_db_per_km
            ),
        )

    def propagate(
        self,
        mu: float,
        alpha: complex,
        distance_km: float,
    ) -> ChannelState:
        """
        Propagate an optical coherent state through the fiber.
        """

        if mu < 0.0:
            raise ValueError(
                "Mean photon number cannot be negative."
            )

        transmission = self.transmittance(
            distance_km
        )

        received_mu = transmission * mu

        received_alpha = (
            np.sqrt(transmission) * alpha
        )

        return ChannelState(
            mu=received_mu,
            alpha=received_alpha,
            distance_km=distance_km,
            transmittance=transmission,
        )

    def __str__(self) -> str:
        return (
            "FiberChannel("
            f"attenuation="
            f"{self.attenuation_db_per_km:.3f} dB/km"
            ")"
        )
