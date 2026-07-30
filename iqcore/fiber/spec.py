"""Fiber specifications shared across the iQuant4 platform.

A :class:`FiberSpec` is the single physical description of an optical fiber
span.  It is deliberately branch-agnostic:

* the **classical** branch (``iq4comm`` long/short-haul links) feeds it to the
  split-step Fourier propagator in :mod:`iqcore.fiber.propagation` to model
  attenuation, chromatic dispersion, and the Kerr nonlinearity;
* the **quantum** branch (QKD key rates, entanglement distribution) reads the
  same object's :meth:`FiberSpec.transmissivity` to parametrize a bosonic loss
  channel.

Keeping one description for both branches is the platform's "shared
foundation": a span defined once behaves identically everywhere it is used.

Engineering (data-sheet) units are used at the interface because that is how
fibers are actually specified; conversions to SI/propagation units happen in
the accessor methods so the rest of the code never re-derives them.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import exp, log, pi

__all__ = ["FiberSpec", "SMF28", "DSF", "LEAF", "DCF", "SPEED_OF_LIGHT_NM_PER_PS"]

# Speed of light expressed in the propagation units used below:
# nanometres per picosecond (c = 2.99792458e8 m/s = 2.99792458e5 nm/ps).
SPEED_OF_LIGHT_NM_PER_PS = 2.99792458e5

# Natural-log conversion between decibels and nepers: 1 dB = (ln10/10) Np.
_DB_TO_NEPER = log(10.0) / 10.0


@dataclass(frozen=True)
class FiberSpec:
    """Physical description of an optical fiber.

    Parameters are given in the engineering units found on manufacturer data
    sheets.  All propagation-facing quantities are exposed through methods so
    every consumer shares one conversion.

    Attributes
    ----------
    attenuation_db_per_km:
        Power attenuation ``alpha`` in dB/km (SMF-28 at 1550 nm ~ 0.2).
    dispersion_ps_nm_km:
        Chromatic-dispersion parameter ``D`` in ps/(nm*km).  Positive is
        anomalous dispersion (the standard-fiber telecom convention).
    dispersion_slope_ps_nm2_km:
        Dispersion slope ``S = dD/dlambda`` in ps/(nm^2*km); sets ``beta3``.
    gamma_per_w_per_km:
        Nonlinear coefficient ``gamma`` in 1/(W*km).
    reference_wavelength_nm:
        Wavelength at which ``D`` and ``S`` are quoted (default 1550 nm).
    core_area_um2:
        Effective mode-field area in um^2 (informational; kept for future
        gamma re-derivation and Raman/EDFA modelling).
    name:
        Human-readable label used in reports and dashboards.
    """

    attenuation_db_per_km: float = 0.2
    dispersion_ps_nm_km: float = 17.0
    dispersion_slope_ps_nm2_km: float = 0.058
    gamma_per_w_per_km: float = 1.3
    reference_wavelength_nm: float = 1550.0
    core_area_um2: float = 80.0
    name: str = "generic-SMF"

    # -- attenuation ----------------------------------------------------
    @property
    def alpha_neper_per_km(self) -> float:
        """Field-power attenuation ``alpha`` in nepers/km (power basis)."""
        return self.attenuation_db_per_km * _DB_TO_NEPER

    def transmissivity(self, length_km: float) -> float:
        """Power transmissivity ``eta`` of a span of ``length_km``.

        ``eta = 10 ** (-alpha_dB * L / 10)`` lies in ``[0, 1]`` and is exactly
        the parameter a quantum bosonic pure-loss channel consumes, so the
        quantum branch never has to re-implement fiber loss.
        """
        if length_km < 0:
            raise ValueError("length_km must be non-negative")
        return 10.0 ** (-self.attenuation_db_per_km * length_km / 10.0)

    def loss_db(self, length_km: float) -> float:
        """Total span loss in dB."""
        return self.attenuation_db_per_km * length_km

    def effective_length_km(self, length_km: float) -> float:
        """Nonlinear effective length ``L_eff = (1 - e^{-alpha L}) / alpha``.

        Reduces to ``length_km`` for a lossless fiber and to ``1/alpha`` for a
        long lossy span; it is the length that governs accumulated nonlinear
        phase.
        """
        if length_km < 0:
            raise ValueError("length_km must be non-negative")
        a = self.alpha_neper_per_km
        if a == 0.0:
            return length_km
        return (1.0 - exp(-a * length_km)) / a

    # -- dispersion -----------------------------------------------------
    def beta2_ps2_per_km(self, wavelength_nm: float | None = None) -> float:
        """Group-velocity dispersion ``beta2`` in ps^2/km.

        Converts the data-sheet ``D`` (ps/nm/km) at ``wavelength`` using
        ``beta2 = -D * lambda^2 / (2*pi*c)``.  The sign convention is the
        standard one: anomalous dispersion (``D > 0``) gives ``beta2 < 0``.
        """
        lam = self.reference_wavelength_nm if wavelength_nm is None else wavelength_nm
        c = SPEED_OF_LIGHT_NM_PER_PS
        return -self.dispersion_ps_nm_km * lam * lam / (2.0 * pi * c)

    def beta3_ps3_per_km(self, wavelength_nm: float | None = None) -> float:
        """Third-order dispersion ``beta3`` in ps^3/km from ``D`` and slope ``S``.

        Uses ``beta3 = (lambda / (2*pi*c^2))^-... `` — concretely
        ``beta3 = (lambda^2 / (2*pi*c)^2) * (lambda^2 * S + 2*lambda*D)``.
        """
        lam = self.reference_wavelength_nm if wavelength_nm is None else wavelength_nm
        c = SPEED_OF_LIGHT_NM_PER_PS
        d = self.dispersion_ps_nm_km
        s = self.dispersion_slope_ps_nm2_km
        pref = (lam * lam) / (2.0 * pi * c) ** 2
        return pref * (lam * lam * s + 2.0 * lam * d)

    def dispersion_length_km(self, pulse_width_ps: float,
                             wavelength_nm: float | None = None) -> float:
        """Dispersion length ``L_D = T0^2 / |beta2|`` for a pulse of width ``T0``.

        ``L_D`` is the propagation distance over which dispersion noticeably
        broadens a pulse; ``float('inf')`` when dispersion is zero.
        """
        b2 = abs(self.beta2_ps2_per_km(wavelength_nm))
        if b2 == 0.0:
            return float("inf")
        return pulse_width_ps * pulse_width_ps / b2

    def nonlinear_length_km(self, peak_power_w: float) -> float:
        """Nonlinear length ``L_NL = 1 / (gamma * P0)``.

        Distance over which the Kerr effect imprints ~1 rad of nonlinear phase;
        ``float('inf')`` when ``gamma`` or the power is zero.
        """
        denom = self.gamma_per_w_per_km * peak_power_w
        if denom == 0.0:
            return float("inf")
        return 1.0 / denom


# -- Standard-fiber presets ---------------------------------------------
# Representative catalogue values at 1550 nm; adjust per data sheet as needed.

#: Standard single-mode fiber (Corning SMF-28 class): the long-haul workhorse.
SMF28 = FiberSpec(
    attenuation_db_per_km=0.20,
    dispersion_ps_nm_km=17.0,
    dispersion_slope_ps_nm2_km=0.058,
    gamma_per_w_per_km=1.3,
    core_area_um2=80.0,
    name="SMF-28",
)

#: Dispersion-shifted fiber: zero dispersion near 1550 nm.
DSF = FiberSpec(
    attenuation_db_per_km=0.22,
    dispersion_ps_nm_km=0.0,
    dispersion_slope_ps_nm2_km=0.07,
    gamma_per_w_per_km=1.6,
    core_area_um2=46.0,
    name="DSF",
)

#: Large-effective-area fiber (LEAF class): low nonlinearity for DWDM.
LEAF = FiberSpec(
    attenuation_db_per_km=0.22,
    dispersion_ps_nm_km=4.0,
    dispersion_slope_ps_nm2_km=0.085,
    gamma_per_w_per_km=0.8,
    core_area_um2=72.0,
    name="LEAF",
)

#: Dispersion-compensating fiber: strong negative dispersion, high loss/gamma.
DCF = FiberSpec(
    attenuation_db_per_km=0.5,
    dispersion_ps_nm_km=-100.0,
    dispersion_slope_ps_nm2_km=-0.34,
    gamma_per_w_per_km=5.0,
    core_area_um2=20.0,
    name="DCF",
)
