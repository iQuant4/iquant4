"""Optical amplifier models for the iQuant4 platform.

An :class:`Amplifier` models a lumped optical amplifier (EDFA-style): it
multiplies the signal field by ``sqrt(G)`` and, optionally, adds amplified
spontaneous emission (ASE) noise set by its noise figure.

Physics conventions
--------------------
* Gain ``G`` and noise figure ``NF`` are given in dB (data-sheet units).
* The spontaneous-emission factor is ``n_sp = NF_lin * G / (2 (G - 1))``; in the
  high-gain limit ``n_sp -> NF_lin / 2``.
* The one-sided ASE power spectral density per polarization is
  ``S_ASE = n_sp * h * nu * (G - 1)`` (W/Hz), with ``h*nu`` the photon energy at
  the amplifier's centre wavelength.
* Reference OSNR accounting uses both polarizations (factor 2); the scalar
  field model carries a single polarization.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

__all__ = ["Amplifier", "PLANCK_J_S", "SPEED_OF_LIGHT_M_PER_S"]

PLANCK_J_S = 6.62607015e-34
SPEED_OF_LIGHT_M_PER_S = 2.99792458e8


@dataclass(frozen=True)
class Amplifier:
    """A lumped optical amplifier (EDFA-style).

    Attributes
    ----------
    gain_db:
        Signal power gain ``G`` in dB.
    noise_figure_db:
        Noise figure ``NF`` in dB (typical EDFA ~ 4-6 dB).
    center_wavelength_nm:
        Operating wavelength for the photon energy (default 1550 nm).
    name:
        Human-readable label.
    """

    gain_db: float
    noise_figure_db: float = 5.0
    center_wavelength_nm: float = 1550.0
    name: str = "EDFA"

    def __post_init__(self) -> None:
        if self.gain_db < 0.0:
            raise ValueError("gain_db must be non-negative")
        if self.noise_figure_db < 0.0:
            raise ValueError("noise_figure_db must be non-negative")

    @property
    def gain_linear(self) -> float:
        return 10.0 ** (self.gain_db / 10.0)

    @property
    def noise_figure_linear(self) -> float:
        return 10.0 ** (self.noise_figure_db / 10.0)

    @property
    def spontaneous_emission_factor(self) -> float:
        """Population-inversion factor ``n_sp`` from the noise figure."""
        g = self.gain_linear
        if g <= 1.0:
            return self.noise_figure_linear / 2.0
        return self.noise_figure_linear * g / (2.0 * (g - 1.0))

    @property
    def photon_energy_j(self) -> float:
        nu = SPEED_OF_LIGHT_M_PER_S / (self.center_wavelength_nm * 1e-9)
        return PLANCK_J_S * nu

    def ase_psd_w_per_hz(self, polarizations: int = 2) -> float:
        """ASE power spectral density (W/Hz) over ``polarizations`` polarizations."""
        g = self.gain_linear
        return (polarizations * self.spontaneous_emission_factor
                * self.photon_energy_j * (g - 1.0))

    def ase_power_w(self, bandwidth_hz: float, polarizations: int = 2) -> float:
        """Total ASE power (W) in ``bandwidth_hz`` over ``polarizations``."""
        return self.ase_psd_w_per_hz(polarizations) * bandwidth_hz

    def amplify(self, field: np.ndarray, grid, *, add_ase: bool = True,
                rng: "np.random.Generator | None" = None,
                polarizations: int = 1) -> np.ndarray:
        """Amplify a field envelope, optionally adding ASE noise.

        The signal is scaled by ``sqrt(G)``.  When ``add_ase`` is true, complex
        Gaussian ASE with power ``S_ASE * B_sim`` (``B_sim = 1/dt`` the
        simulation bandwidth) is added; the scalar field carries one
        polarization by default.  Pass an ``rng`` for reproducibility.
        """
        g_amp = np.sqrt(self.gain_linear)
        out = g_amp * np.asarray(field, dtype=np.complex128)
        if add_ase:
            if rng is None:
                rng = np.random.default_rng()
            dt_s = grid.dt_ps * 1e-12
            bandwidth_hz = 1.0 / dt_s
            variance = self.ase_psd_w_per_hz(polarizations) * bandwidth_hz
            noise = np.sqrt(variance / 2.0) * (
                rng.standard_normal(out.shape)
                + 1j * rng.standard_normal(out.shape))
            out = out + noise
        return out

    def __str__(self) -> str:
        return (f"Amplifier({self.name}, gain={self.gain_db:.1f} dB, "
                f"NF={self.noise_figure_db:.1f} dB)")
