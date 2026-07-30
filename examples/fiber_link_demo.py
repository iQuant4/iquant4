"""Realistic fiber-link demo for the iQuant4 platform.

Runs a 10 ps Gaussian pulse through 80 km of SMF-28 and reports how the three
physical effects -- attenuation, chromatic dispersion, and the Kerr
nonlinearity -- reshape it, then shows the shared-foundation link with the
quantum branch via the span transmissivity.

Run:
    python -m examples.fiber_link_demo
or:
    python examples/fiber_link_demo.py
"""

from __future__ import annotations

import numpy as np

from iqcore.fiber import TimeGrid, gaussian_pulse, propagate, SMF28


def _rms_width_ps(field: np.ndarray, grid: TimeGrid) -> float:
    t = grid.time_ps
    p = np.abs(field) ** 2
    n = p.sum()
    m = (t * p).sum() / n
    return float(np.sqrt(((t - m) ** 2 * p).sum() / n))


def main() -> None:
    grid = TimeGrid(num_points=8192, dt_ps=0.2)
    peak_power_w = 20e-3          # 20 mW launch (13 dBm) -- nonlinearity visible
    width_ps = 10.0
    length_km = 80.0
    fiber = SMF28

    pulse = gaussian_pulse(grid, peak_power_w=peak_power_w, width_ps=width_ps)
    full = propagate(pulse, grid, fiber, length_km)
    disp_only = propagate(pulse, grid, fiber, length_km,
                          include_nonlinearity=False)

    print(f"Fiber: {fiber.name}  |  span: {length_km:.0f} km  |  launch: "
          f"{10*np.log10(peak_power_w/1e-3):.1f} dBm")
    print(f"  beta2               = {fiber.beta2_ps2_per_km():+.4f} ps^2/km")
    print(f"  dispersion length   = {fiber.dispersion_length_km(width_ps):.2f} km")
    print(f"  nonlinear length    = {fiber.nonlinear_length_km(peak_power_w):.2f} km")
    print(f"  effective length    = {fiber.effective_length_km(length_km):.2f} km")
    print(f"  span loss           = {full.loss_db:.2f} dB")
    print()
    print(f"  input  RMS width    = {_rms_width_ps(pulse, grid):.2f} ps")
    print(f"  output RMS (disp)   = {_rms_width_ps(disp_only.field, grid):.2f} ps")
    print(f"  output RMS (full)   = {_rms_width_ps(full.field, grid):.2f} ps")
    print(f"  split-steps used    = {full.num_steps}")
    print()
    # Shared-foundation bridge to the quantum branch:
    eta = fiber.transmissivity(length_km)
    print(f"  quantum-channel transmissivity eta(80 km) = {eta:.4f}")
    print("  (the same FiberSpec parametrizes a bosonic loss channel for QKD)")


if __name__ == "__main__":
    main()
