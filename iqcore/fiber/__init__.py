"""Realistic fiber modelling for the iQuant4 platform.

This subpackage is the shared physical-layer foundation used by both the
classical optical-communications branch and the quantum-communications branch:

* :class:`FiberSpec` and the standard-fiber presets (:data:`SMF28`,
  :data:`DSF`, :data:`LEAF`, :data:`DCF`) describe a span once, in data-sheet
  units, and expose everything downstream code needs -- ``beta2``/``beta3``,
  effective length, and the power ``transmissivity`` a quantum loss channel
  consumes.
* :func:`propagate` solves the nonlinear Schrodinger equation with a symmetric
  split-step Fourier method (attenuation, chromatic dispersion, Kerr
  nonlinearity).
* :class:`Amplifier` models EDFA-style gain and ASE noise, and :class:`Link`
  chains spans and amplifiers into a full multi-span system with OSNR and
  end-to-end transmissivity.

Example
-------
>>> import numpy as np
>>> from iqcore.fiber import TimeGrid, gaussian_pulse, propagate, SMF28
>>> grid = TimeGrid(num_points=4096, dt_ps=0.5)
>>> pulse = gaussian_pulse(grid, peak_power_w=1e-3, width_ps=10.0)
>>> result = propagate(pulse, grid, SMF28, length_km=80.0)
>>> round(result.loss_db, 2)
16.0
"""

from __future__ import annotations

from .spec import (
    FiberSpec,
    SMF28,
    DSF,
    LEAF,
    DCF,
    SPEED_OF_LIGHT_NM_PER_PS,
)
from .propagation import (
    TimeGrid,
    gaussian_pulse,
    soliton_pulse,
    propagate,
    PropagationResult,
)
from .amplifier import Amplifier
from .link import FiberSpan, Link
from .nonlinear import backpropagate, compensate_dispersion, nmse
from .wdm import (
    WDMChannel,
    DWDMGrid,
    CWDMGrid,
    WDMComb,
    dwdm_frequency_hz,
    dwdm_wavelength_nm,
    frequency_to_wavelength_nm,
    wavelength_nm_to_frequency_hz,
    CWDM_WAVELENGTHS_NM,
    C_BAND_NM,
)

__all__ = [
    "FiberSpec",
    "SMF28",
    "DSF",
    "LEAF",
    "DCF",
    "SPEED_OF_LIGHT_NM_PER_PS",
    "TimeGrid",
    "gaussian_pulse",
    "soliton_pulse",
    "propagate",
    "PropagationResult",
    "Amplifier",
    "FiberSpan",
    "Link",
    "backpropagate",
    "compensate_dispersion",
    "nmse",
    "WDMChannel",
    "DWDMGrid",
    "CWDMGrid",
    "WDMComb",
    "dwdm_frequency_hz",
    "dwdm_wavelength_nm",
    "frequency_to_wavelength_nm",
    "wavelength_nm_to_frequency_hz",
    "CWDM_WAVELENGTHS_NM",
    "C_BAND_NM",
]
