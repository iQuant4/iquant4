"""Multi-span optical link assembly for the iQuant4 platform.

A :class:`Link` is an ordered chain of physical elements -- fiber spans and
amplifiers -- that a signal traverses in sequence.  It is the object that turns
the single-span :mod:`iqcore.fiber` primitives into a realistic long-haul
system, and it is a shared-foundation citizen:

* the **classical** branch calls :meth:`Link.propagate_field` to push an optical
  field through every span (split-step Fourier) and amplifier (gain + ASE), and
  :meth:`Link.osnr_db` for the optical signal-to-noise ratio;
* the **quantum** branch reads :attr:`Link.passive_transmissivity` -- the net
  loss of the fiber spans -- to parametrize an end-to-end bosonic loss channel
  for QKD key-rate-versus-distance analysis.

Example
-------
>>> from iqcore.fiber import Link, Amplifier, SMF28
>>> link = Link()
>>> for _ in range(10):
...     link.span(SMF28, 80.0).amplifier(Amplifier(gain_db=16.0, noise_figure_db=5.0))
...
>>> round(link.total_length_km, 0)
800.0
>>> round(link.osnr_db(launch_power_w=1e-3), 1)   # 0 dBm launch
25.0
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .amplifier import Amplifier
from .propagation import TimeGrid, propagate
from .spec import FiberSpec

__all__ = ["FiberSpan", "Link"]


@dataclass(frozen=True)
class FiberSpan:
    """One fiber span in a link."""

    fiber: FiberSpec
    length_km: float
    wavelength_nm: float | None = None


class Link:
    """An ordered chain of fiber spans and amplifiers.

    Parameters
    ----------
    reference_bandwidth_hz:
        Optical reference bandwidth for OSNR (default 12.5 GHz ~ 0.1 nm at
        1550 nm, the telecom convention).
    """

    def __init__(self, *, reference_bandwidth_hz: float = 12.5e9) -> None:
        self.elements: list[object] = []
        self.reference_bandwidth_hz = reference_bandwidth_hz

    # -- builder API (chainable) ----------------------------------------
    def span(self, fiber: FiberSpec, length_km: float,
             wavelength_nm: float | None = None) -> "Link":
        self.elements.append(FiberSpan(fiber, length_km, wavelength_nm))
        return self

    def amplifier(self, amp: Amplifier) -> "Link":
        self.elements.append(amp)
        return self

    # -- geometry / accounting ------------------------------------------
    @property
    def spans(self) -> list[FiberSpan]:
        return [e for e in self.elements if isinstance(e, FiberSpan)]

    @property
    def amplifiers(self) -> list[Amplifier]:
        return [e for e in self.elements if isinstance(e, Amplifier)]

    @property
    def total_length_km(self) -> float:
        return sum(s.length_km for s in self.spans)

    @property
    def passive_transmissivity(self) -> float:
        """Net power transmissivity of the fiber spans only (no amplifiers).

        This is the parameter the quantum branch consumes: amplifiers add noise
        but do not restore quantum coherence, so the end-to-end *loss* seen by a
        QKD analysis is the product of the span transmissivities.
        """
        eta = 1.0
        for s in self.spans:
            eta *= s.fiber.transmissivity(s.length_km)
        return eta

    @property
    def net_gain_db(self) -> float:
        """Net signal power change in dB, spans and amplifiers combined."""
        gain_linear = 1.0
        for e in self.elements:
            if isinstance(e, FiberSpan):
                gain_linear *= e.fiber.transmissivity(e.length_km)
            else:  # Amplifier
                gain_linear *= e.gain_linear
        return 10.0 * np.log10(gain_linear)

    # -- optical signal-to-noise ratio ----------------------------------
    def osnr_db(self, launch_power_w: float) -> float:
        """End-to-end OSNR (dB) for a given launch power.

        Walks the chain tracking signal and accumulated ASE power: a span
        attenuates both; an amplifier multiplies both by its gain and adds fresh
        two-polarization ASE in the reference bandwidth.  For a chain of
        identical loss-compensated spans this reproduces the textbook
        ``OSNR = P_launch - L_span - NF - 10log10(h*nu*B) - 10log10(N)``.
        """
        if launch_power_w <= 0:
            raise ValueError("launch_power_w must be positive")
        signal = launch_power_w
        ase = 0.0
        for e in self.elements:
            if isinstance(e, FiberSpan):
                eta = e.fiber.transmissivity(e.length_km)
                signal *= eta
                ase *= eta
            else:  # Amplifier
                signal *= e.gain_linear
                ase = ase * e.gain_linear + e.ase_power_w(
                    self.reference_bandwidth_hz, polarizations=2)
        if ase <= 0.0:
            return float("inf")
        return 10.0 * np.log10(signal / ase)

    # -- field propagation ----------------------------------------------
    def propagate_field(self, field: np.ndarray, grid: TimeGrid, *,
                        add_ase: bool = True,
                        rng: "np.random.Generator | None" = None) -> np.ndarray:
        """Propagate an optical field through the whole link, element by element."""
        if add_ase and rng is None:
            rng = np.random.default_rng()
        out = np.asarray(field, dtype=np.complex128)
        for e in self.elements:
            if isinstance(e, FiberSpan):
                out = propagate(out, grid, e.fiber, e.length_km,
                                wavelength_nm=e.wavelength_nm).field
            else:  # Amplifier
                out = e.amplify(out, grid, add_ase=add_ase, rng=rng)
        return out

    def __repr__(self) -> str:
        return (f"Link({len(self.spans)} spans, {len(self.amplifiers)} amps, "
                f"{self.total_length_km:.0f} km)")
