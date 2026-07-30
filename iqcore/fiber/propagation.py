"""Split-step Fourier propagation of optical fields through fiber.

This module solves the scalar nonlinear Schrodinger equation (NLSE) that
governs pulse propagation in a single-mode fiber:

.. math::

    \\frac{\\partial A}{\\partial z}
      = -\\frac{\\alpha}{2} A
        - i\\frac{\\beta_2}{2}\\frac{\\partial^2 A}{\\partial T^2}
        + \\frac{\\beta_3}{6}\\frac{\\partial^3 A}{\\partial T^3}
        + i\\gamma |A|^2 A ,

where ``A(z, T)`` is the slowly varying complex field envelope in a frame
co-moving with the pulse, ``T`` is retarded time, and the coefficients come
from a :class:`~iqcore.fiber.spec.FiberSpec`.

The symmetric (Strang) split-step method advances the field over each step by
alternating a purely *linear* half-step (attenuation + dispersion, applied in
the frequency domain) with a *nonlinear* full-step (self-phase modulation,
applied in the time domain):

    exp(D dz/2) -> exp(N dz) -> exp(D dz/2)

which is second-order accurate in the step size ``dz``.

Field amplitude convention: ``A`` is in units of sqrt(W), so instantaneous
optical power is ``|A|^2`` in watts and pulse energy is ``sum |A|^2 * dt``.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .spec import FiberSpec

__all__ = ["TimeGrid", "gaussian_pulse", "soliton_pulse", "propagate", "PropagationResult"]


@dataclass(frozen=True)
class TimeGrid:
    """Uniform temporal sampling grid and its matching angular-frequency axis.

    Parameters
    ----------
    num_points:
        Number of samples (a power of two is fastest for the FFT).
    dt_ps:
        Sample spacing in picoseconds.
    """

    num_points: int
    dt_ps: float

    def __post_init__(self) -> None:
        if self.num_points < 2:
            raise ValueError("num_points must be >= 2")
        if self.dt_ps <= 0:
            raise ValueError("dt_ps must be positive")

    @property
    def time_ps(self) -> np.ndarray:
        """Centered time axis in ps, spanning the sampling window."""
        n = self.num_points
        return (np.arange(n) - n // 2) * self.dt_ps

    @property
    def omega_rad_per_ps(self) -> np.ndarray:
        """Angular-frequency axis (rad/ps), FFT-ordered to match ``numpy.fft``."""
        return 2.0 * np.pi * np.fft.fftfreq(self.num_points, d=self.dt_ps)

    @property
    def window_ps(self) -> float:
        return self.num_points * self.dt_ps


def gaussian_pulse(grid: TimeGrid, peak_power_w: float, width_ps: float,
                   chirp: float = 0.0, center_ps: float = 0.0) -> np.ndarray:
    """Chirped Gaussian field envelope ``A(T)`` in sqrt(W).

    ``A = sqrt(P0) * exp(-(1 + i C)/2 * (T - T_c)^2 / T0^2)`` where ``T0`` is
    the ``1/e`` field half-width (``width_ps``) and ``C`` is the chirp.
    """
    if width_ps <= 0:
        raise ValueError("width_ps must be positive")
    t = grid.time_ps - center_ps
    envelope = np.exp(-(1.0 + 1j * chirp) * 0.5 * (t / width_ps) ** 2)
    return np.sqrt(peak_power_w) * envelope.astype(np.complex128)


def soliton_pulse(grid: TimeGrid, fiber: FiberSpec, width_ps: float,
                  order: int = 1, wavelength_nm: float | None = None,
                  center_ps: float = 0.0) -> np.ndarray:
    """Fundamental (or higher-order) soliton ``A(T) = sqrt(P0) sech(T/T0)``.

    The peak power is chosen so the soliton order ``N`` satisfies
    ``N^2 = gamma P0 T0^2 / |beta2|``.  A fundamental soliton (``order=1``)
    propagates without changing shape in a lossless fiber, which makes it a
    stringent test of the dispersion/nonlinearity balance.
    """
    b2 = fiber.beta2_ps2_per_km(wavelength_nm)
    gamma = fiber.gamma_per_w_per_km
    if gamma <= 0:
        raise ValueError("soliton requires gamma > 0")
    if b2 >= 0:
        raise ValueError("soliton requires anomalous dispersion (beta2 < 0)")
    peak_power_w = (order ** 2) * abs(b2) / (gamma * width_ps ** 2)
    t = grid.time_ps - center_ps
    envelope = 1.0 / np.cosh(t / width_ps)
    return np.sqrt(peak_power_w) * envelope.astype(np.complex128)


@dataclass(frozen=True)
class PropagationResult:
    """Outcome of a fiber propagation.

    Attributes
    ----------
    field:
        Output complex envelope on the same :class:`TimeGrid`.
    input_energy_pj, output_energy_pj:
        Pulse energies (pJ) before and after the span.
    num_steps:
        Number of split-step iterations actually used.
    fiber_name, length_km:
        Provenance of the run.
    """

    field: np.ndarray
    input_energy_pj: float
    output_energy_pj: float
    num_steps: int
    fiber_name: str
    length_km: float

    @property
    def loss_db(self) -> float:
        """Measured end-to-end power loss in dB."""
        if self.output_energy_pj <= 0:
            return float("inf")
        return 10.0 * np.log10(self.input_energy_pj / self.output_energy_pj)


def _pulse_energy_pj(field: np.ndarray, dt_ps: float) -> float:
    # |A|^2 is power in W, dt in ps -> energy in W*ps = pJ.
    return float(np.sum(np.abs(field) ** 2) * dt_ps)


def _auto_step_count(fiber: FiberSpec, length_km: float, field: np.ndarray,
                     grid: TimeGrid, wavelength_nm: float | None,
                     phase_per_step: float) -> int:
    """Choose a step count that keeps the per-step nonlinear phase small.

    The dominant split-step error scales with the nonlinear phase accumulated
    per step; bounding it to ``phase_per_step`` radians gives an accurate,
    self-tuning default.
    """
    peak_power = float(np.max(np.abs(field) ** 2))
    l_nl = fiber.nonlinear_length_km(peak_power)
    steps_nl = length_km / (phase_per_step * l_nl) if np.isfinite(l_nl) else 0.0
    # Also resolve dispersion over a reasonable number of steps.
    steps_floor = 20.0
    return int(max(steps_floor, np.ceil(steps_nl)))


def propagate(field: np.ndarray, grid: TimeGrid, fiber: FiberSpec,
              length_km: float, *, num_steps: int | None = None,
              wavelength_nm: float | None = None,
              include_loss: bool = True, include_dispersion: bool = True,
              include_nonlinearity: bool = True,
              phase_per_step: float = 5e-3) -> PropagationResult:
    """Propagate ``field`` through ``length_km`` of ``fiber`` via split-step Fourier.

    Parameters
    ----------
    field:
        Input complex envelope (sqrt(W)) sampled on ``grid``.
    grid:
        The :class:`TimeGrid` the field lives on.
    fiber:
        Physical :class:`~iqcore.fiber.spec.FiberSpec`.
    length_km:
        Span length.
    num_steps:
        Fixed number of split-step iterations; if ``None`` an accuracy-based
        count is chosen from the nonlinear phase per step.
    include_loss, include_dispersion, include_nonlinearity:
        Toggle individual physical effects.  Turning effects off is useful for
        validation (e.g. pure dispersion has a closed-form solution).
    phase_per_step:
        Target maximum nonlinear phase (rad) per step when ``num_steps`` is
        auto-selected.

    Returns
    -------
    PropagationResult
    """
    if length_km < 0:
        raise ValueError("length_km must be non-negative")
    a = np.asarray(field, dtype=np.complex128)
    if a.shape != (grid.num_points,):
        raise ValueError("field shape must match grid.num_points")

    input_energy = _pulse_energy_pj(a, grid.dt_ps)

    if length_km == 0.0:
        return PropagationResult(a.copy(), input_energy, input_energy, 0,
                                 fiber.name, 0.0)

    if num_steps is None:
        num_steps = _auto_step_count(fiber, length_km, a, grid,
                                     wavelength_nm, phase_per_step)
    if num_steps < 1:
        num_steps = 1
    dz = length_km / num_steps

    # Linear operator in the frequency domain: attenuation + dispersion.
    omega = grid.omega_rad_per_ps
    alpha = fiber.alpha_neper_per_km if include_loss else 0.0
    b2 = fiber.beta2_ps2_per_km(wavelength_nm) if include_dispersion else 0.0
    b3 = fiber.beta3_ps3_per_km(wavelength_nm) if include_dispersion else 0.0
    # dA/dz = [ -alpha/2 + i (beta2/2) omega^2 - i (beta3/6) omega^3 ] A
    # (the sign of the dispersion term follows from A_TT -> -omega^2 under this
    #  FFT convention).
    linear_op = (-alpha / 2.0
                 + 1j * (b2 / 2.0) * omega ** 2
                 - 1j * (b3 / 6.0) * omega ** 3)
    half_step_lin = np.exp(linear_op * (dz / 2.0))

    gamma = fiber.gamma_per_w_per_km if include_nonlinearity else 0.0

    # Symmetric split-step: half linear, full nonlinear, half linear.
    a_freq = np.fft.fft(a)
    for _ in range(num_steps):
        a_freq *= half_step_lin
        a_time = np.fft.ifft(a_freq)
        if gamma != 0.0:
            a_time *= np.exp(1j * gamma * np.abs(a_time) ** 2 * dz)
        a_freq = np.fft.fft(a_time)
        a_freq *= half_step_lin
    a_out = np.fft.ifft(a_freq)

    output_energy = _pulse_energy_pj(a_out, grid.dt_ps)
    return PropagationResult(a_out, input_energy, output_energy, num_steps,
                             fiber.name, length_km)
