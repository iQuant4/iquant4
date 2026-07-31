"""Nonlinear compensation for the iQuant4 platform: digital backpropagation.

Digital backpropagation (DBP) inverts the nonlinear Schrodinger equation.  Where
:func:`iqcore.fiber.propagate` sends a field *forward* through fiber (loss,
dispersion, Kerr), :func:`backpropagate` runs the *inverse* channel -- gain
instead of loss, negated dispersion, negated Kerr phase -- with the same
symmetric split-step scheme.  Applied to a received field it removes both
chromatic dispersion and deterministic nonlinear distortion, recovering the
launched field up to split-step discretisation error.

For comparison, :func:`compensate_dispersion` performs *linear* (dispersion-only)
equalisation: a single exact all-pass frequency-domain multiply.  DBP reduces to
this when the nonlinearity is switched off, and beats it whenever the Kerr effect
is significant.
"""

from __future__ import annotations

import numpy as np

from .propagation import PropagationResult, TimeGrid, _pulse_energy_pj
from .spec import FiberSpec

__all__ = ["backpropagate", "compensate_dispersion", "nmse"]


def nmse(estimate: np.ndarray, reference: np.ndarray) -> float:
    """Normalised mean-square error ``||estimate - reference||^2 / ||reference||^2``."""
    estimate = np.asarray(estimate, dtype=np.complex128)
    reference = np.asarray(reference, dtype=np.complex128)
    denom = float(np.sum(np.abs(reference) ** 2))
    if denom == 0.0:
        raise ValueError("reference has zero energy")
    return float(np.sum(np.abs(estimate - reference) ** 2) / denom)


def compensate_dispersion(field: np.ndarray, grid: TimeGrid, fiber: FiberSpec,
                          length_km: float, *,
                          wavelength_nm: float | None = None) -> np.ndarray:
    """Exact linear (chromatic-dispersion) equalisation over ``length_km``.

    Applies the inverse of the fiber's all-pass dispersion transfer function in
    one frequency-domain multiply -- the standard linear equaliser and the
    baseline that DBP must beat.
    """
    omega = grid.omega_rad_per_ps
    b2 = fiber.beta2_ps2_per_km(wavelength_nm)
    b3 = fiber.beta3_ps3_per_km(wavelength_nm)
    # Forward dispersion phase over L is exp(i(b2/2)w^2 L - i(b3/6)w^3 L);
    # the inverse is its complex conjugate.
    forward = (1j * (b2 / 2.0) * omega ** 2 - 1j * (b3 / 6.0) * omega ** 3) * length_km
    a_freq = np.fft.fft(np.asarray(field, dtype=np.complex128))
    a_freq *= np.exp(-forward)
    return np.fft.ifft(a_freq)


def backpropagate(field: np.ndarray, grid: TimeGrid, fiber: FiberSpec,
                  length_km: float, *, num_steps: int | None = None,
                  wavelength_nm: float | None = None,
                  include_loss: bool = True, include_dispersion: bool = True,
                  include_nonlinearity: bool = True,
                  phase_per_step: float = 5e-3) -> PropagationResult:
    """Digitally backpropagate ``field`` through ``length_km`` of ``fiber``.

    Solves the inverse NLSE with a symmetric split-step scheme: each step applies
    a half inverse-linear operator (gain + negated dispersion), a full inverse
    Kerr phase, and another half inverse-linear operator.  With
    ``include_nonlinearity=False`` this is exact linear dispersion compensation.

    Returns a :class:`~iqcore.fiber.propagation.PropagationResult` whose ``field``
    is the recovered launch field.
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
        peak_power = float(np.max(np.abs(a) ** 2))
        l_nl = fiber.nonlinear_length_km(peak_power)
        steps_nl = length_km / (phase_per_step * l_nl) if np.isfinite(l_nl) else 0.0
        num_steps = int(max(20.0, np.ceil(steps_nl)))
    num_steps = max(1, num_steps)
    dz = length_km / num_steps

    omega = grid.omega_rad_per_ps
    alpha = fiber.alpha_neper_per_km if include_loss else 0.0
    b2 = fiber.beta2_ps2_per_km(wavelength_nm) if include_dispersion else 0.0
    b3 = fiber.beta3_ps3_per_km(wavelength_nm) if include_dispersion else 0.0
    # Forward linear operator was  L = -alpha/2 + i(b2/2)w^2 - i(b3/6)w^3.
    # The inverse channel uses -L: gain (+alpha/2) and negated dispersion.
    linear_op = (-alpha / 2.0
                 + 1j * (b2 / 2.0) * omega ** 2
                 - 1j * (b3 / 6.0) * omega ** 3)
    half_step_inv = np.exp(-linear_op * (dz / 2.0))

    gamma = fiber.gamma_per_w_per_km if include_nonlinearity else 0.0

    a_freq = np.fft.fft(a)
    for _ in range(num_steps):
        a_freq *= half_step_inv
        a_time = np.fft.ifft(a_freq)
        if gamma != 0.0:
            a_time *= np.exp(-1j * gamma * np.abs(a_time) ** 2 * dz)
        a_freq = np.fft.fft(a_time)
        a_freq *= half_step_inv
    a_out = np.fft.ifft(a_freq)

    output_energy = _pulse_energy_pj(a_out, grid.dt_ps)
    return PropagationResult(a_out, input_energy, output_energy, num_steps,
                             fiber.name, length_km)
