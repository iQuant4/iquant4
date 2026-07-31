"""Wavelength-division multiplexing (WDM) grids for the iQuant4 platform.

Physical-layer, shared by both branches.  Implements the two ITU-T standard
grids:

* **DWDM** -- ITU-T G.694.1: a *frequency* grid anchored at 193.1 THz with
  nominal channel spacings of 12.5, 25, 50 or 100 GHz.  Channel ``n`` sits at
  ``f = 193.1 THz + n * spacing``.
* **CWDM** -- ITU-T G.694.2: a *wavelength* grid of 18 channels from 1271 nm to
  1611 nm on a 20 nm spacing.

The module exposes plain functions (for quick lookups), immutable
:class:`WDMChannel` objects, the :class:`DWDMGrid` / :class:`CWDMGrid` grids,
and a :class:`WDMComb` -- an ordered set of channels with per-channel launch
power, which is what a multi-channel transmitter or an EDFA sees.

Example
-------
>>> from iqcore.fiber import DWDMGrid
>>> grid = DWDMGrid(spacing_ghz=100.0)
>>> round(grid.wavelength_nm(0), 2)      # anchor channel
1552.52
>>> round(grid.frequency_thz(0), 4)
193.1
"""

from __future__ import annotations

from dataclasses import dataclass, field

__all__ = [
    "SPEED_OF_LIGHT_M_PER_S",
    "DWDM_ANCHOR_HZ",
    "DWDM_SPACINGS_GHZ",
    "CWDM_WAVELENGTHS_NM",
    "C_BAND_NM",
    "dwdm_frequency_hz",
    "dwdm_wavelength_nm",
    "frequency_to_wavelength_nm",
    "wavelength_nm_to_frequency_hz",
    "WDMChannel",
    "DWDMGrid",
    "CWDMGrid",
    "WDMComb",
]

SPEED_OF_LIGHT_M_PER_S = 2.99792458e8

# ITU-T G.694.1 anchor frequency.
DWDM_ANCHOR_HZ = 193.1e12
DWDM_SPACINGS_GHZ = (12.5, 25.0, 50.0, 100.0)

# ITU-T G.694.2 CWDM nominal wavelengths (nm): 1271..1611 on a 20 nm grid.
CWDM_WAVELENGTHS_NM = tuple(float(1271 + 20 * i) for i in range(18))

# Conventional C-band edges (nm) -- the usable EDFA window.
C_BAND_NM = (1530.0, 1565.0)


def frequency_to_wavelength_nm(frequency_hz: float) -> float:
    """Vacuum wavelength (nm) of an optical frequency (Hz)."""
    if frequency_hz <= 0.0:
        raise ValueError("frequency_hz must be positive")
    return SPEED_OF_LIGHT_M_PER_S / frequency_hz * 1e9


def wavelength_nm_to_frequency_hz(wavelength_nm: float) -> float:
    """Optical frequency (Hz) of a vacuum wavelength (nm)."""
    if wavelength_nm <= 0.0:
        raise ValueError("wavelength_nm must be positive")
    return SPEED_OF_LIGHT_M_PER_S / (wavelength_nm * 1e-9)


def dwdm_frequency_hz(channel: int, spacing_ghz: float = 100.0,
                      anchor_hz: float = DWDM_ANCHOR_HZ) -> float:
    """Frequency (Hz) of DWDM ``channel`` relative to the 193.1 THz anchor."""
    return anchor_hz + channel * spacing_ghz * 1e9


def dwdm_wavelength_nm(channel: int, spacing_ghz: float = 100.0,
                       anchor_hz: float = DWDM_ANCHOR_HZ) -> float:
    """Vacuum wavelength (nm) of DWDM ``channel``."""
    return frequency_to_wavelength_nm(
        dwdm_frequency_hz(channel, spacing_ghz, anchor_hz))


@dataclass(frozen=True)
class WDMChannel:
    """A single optical carrier, identified by its frequency.

    ``index`` is the grid channel number (if it came from a grid) and ``power_w``
    is an optional launch power carried alongside the carrier.
    """

    frequency_hz: float
    index: int | None = None
    power_w: float = 0.0
    label: str = ""

    def __post_init__(self) -> None:
        if self.frequency_hz <= 0.0:
            raise ValueError("frequency_hz must be positive")
        if self.power_w < 0.0:
            raise ValueError("power_w must be non-negative")

    @property
    def wavelength_nm(self) -> float:
        return frequency_to_wavelength_nm(self.frequency_hz)

    @property
    def frequency_thz(self) -> float:
        return self.frequency_hz / 1e12

    @property
    def power_dbm(self) -> float:
        if self.power_w <= 0.0:
            return float("-inf")
        return 10.0 * _log10(self.power_w * 1e3)

    def in_c_band(self) -> bool:
        lo, hi = C_BAND_NM
        return lo <= self.wavelength_nm <= hi


class DWDMGrid:
    """ITU-T G.694.1 dense WDM frequency grid.

    Parameters
    ----------
    spacing_ghz:
        Nominal channel spacing (must be one of 12.5, 25, 50, 100 GHz).
    anchor_hz:
        Reference frequency (default 193.1 THz).
    """

    def __init__(self, spacing_ghz: float = 50.0,
                 anchor_hz: float = DWDM_ANCHOR_HZ) -> None:
        if spacing_ghz not in DWDM_SPACINGS_GHZ:
            raise ValueError(
                f"spacing_ghz must be one of {DWDM_SPACINGS_GHZ}")
        self.spacing_ghz = float(spacing_ghz)
        self.anchor_hz = float(anchor_hz)

    def frequency_hz(self, channel: int) -> float:
        return dwdm_frequency_hz(channel, self.spacing_ghz, self.anchor_hz)

    def frequency_thz(self, channel: int) -> float:
        return self.frequency_hz(channel) / 1e12

    def wavelength_nm(self, channel: int) -> float:
        return frequency_to_wavelength_nm(self.frequency_hz(channel))

    def channel(self, index: int, power_w: float = 0.0) -> WDMChannel:
        return WDMChannel(
            frequency_hz=self.frequency_hz(index),
            index=index,
            power_w=power_w,
            label=f"DWDM{index:+d}@{self.spacing_ghz:g}GHz",
        )

    def nearest_index(self, *, wavelength_nm: float | None = None,
                      frequency_hz: float | None = None) -> int:
        """Nearest integer channel index to a wavelength or frequency."""
        if (wavelength_nm is None) == (frequency_hz is None):
            raise ValueError("give exactly one of wavelength_nm / frequency_hz")
        if frequency_hz is None:
            frequency_hz = wavelength_nm_to_frequency_hz(wavelength_nm)
        return round((frequency_hz - self.anchor_hz) / (self.spacing_ghz * 1e9))

    def channels(self, start: int, stop: int,
                 power_w: float = 0.0) -> list[WDMChannel]:
        """Channels for indices ``start..stop`` inclusive."""
        return [self.channel(n, power_w) for n in range(start, stop + 1)]

    def c_band_channels(self, power_w: float = 0.0) -> list[WDMChannel]:
        """All grid channels whose wavelength falls inside the C-band."""
        lo_nm, hi_nm = C_BAND_NM
        # Higher frequency -> shorter wavelength, so scan a generous index range.
        f_hi = wavelength_nm_to_frequency_hz(lo_nm)
        f_lo = wavelength_nm_to_frequency_hz(hi_nm)
        n_lo = self.nearest_index(frequency_hz=f_lo)
        n_hi = self.nearest_index(frequency_hz=f_hi)
        out = []
        for n in range(min(n_lo, n_hi) - 1, max(n_lo, n_hi) + 2):
            ch = self.channel(n, power_w)
            if ch.in_c_band():
                out.append(ch)
        return sorted(out, key=lambda c: c.frequency_hz)

    def __repr__(self) -> str:
        return f"DWDMGrid(spacing={self.spacing_ghz:g} GHz)"


class CWDMGrid:
    """ITU-T G.694.2 coarse WDM wavelength grid (18 channels, 20 nm spacing)."""

    wavelengths_nm = CWDM_WAVELENGTHS_NM

    def wavelength_nm(self, channel: int) -> float:
        return self.wavelengths_nm[channel]

    def frequency_hz(self, channel: int) -> float:
        return wavelength_nm_to_frequency_hz(self.wavelengths_nm[channel])

    def channel(self, index: int, power_w: float = 0.0) -> WDMChannel:
        return WDMChannel(
            frequency_hz=self.frequency_hz(index),
            index=index,
            power_w=power_w,
            label=f"CWDM{int(self.wavelengths_nm[index])}nm",
        )

    def channels(self, power_w: float = 0.0) -> list[WDMChannel]:
        return [self.channel(i, power_w) for i in range(len(self.wavelengths_nm))]

    def nearest_index(self, wavelength_nm: float) -> int:
        return min(range(len(self.wavelengths_nm)),
                   key=lambda i: abs(self.wavelengths_nm[i] - wavelength_nm))

    def __repr__(self) -> str:
        return f"CWDMGrid({len(self.wavelengths_nm)} channels)"


@dataclass
class WDMComb:
    """An ordered set of WDM channels with per-channel launch power.

    This is what a multi-channel transmitter emits and what an amplifier sees:
    the aggregate the link must carry.
    """

    channels: list[WDMChannel] = field(default_factory=list)

    @classmethod
    def uniform(cls, grid: "DWDMGrid", start: int, stop: int,
                power_dbm_per_channel: float = 0.0) -> "WDMComb":
        """A comb of equal-power channels across a DWDM index range."""
        p_w = 1e-3 * 10.0 ** (power_dbm_per_channel / 10.0)
        return cls(grid.channels(start, stop, power_w=p_w))

    @property
    def num_channels(self) -> int:
        return len(self.channels)

    @property
    def total_power_w(self) -> float:
        return sum(c.power_w for c in self.channels)

    @property
    def total_power_dbm(self) -> float:
        p = self.total_power_w
        return 10.0 * _log10(p * 1e3) if p > 0 else float("-inf")

    @property
    def center_frequency_hz(self) -> float:
        if not self.channels:
            raise ValueError("empty comb")
        return sum(c.frequency_hz for c in self.channels) / len(self.channels)

    @property
    def occupied_bandwidth_hz(self) -> float:
        """Span from lowest to highest carrier frequency."""
        if len(self.channels) < 2:
            return 0.0
        freqs = [c.frequency_hz for c in self.channels]
        return max(freqs) - min(freqs)

    def __len__(self) -> int:
        return len(self.channels)

    def __repr__(self) -> str:
        return (f"WDMComb({self.num_channels} ch, "
                f"{self.total_power_dbm:.1f} dBm total)")


def _log10(x: float) -> float:
    # Local import keeps module import cost trivial and avoids a hard numpy dep.
    from math import log10
    return log10(x)
