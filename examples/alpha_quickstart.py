"""Headless quick start covering both active iQuant4 alpha packages."""

from __future__ import annotations

import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import numpy as np

import iq4comm as iqc
import iqcore as iq


def main() -> None:
    cat_state = iq.states.even_cat_state(alpha=1.5, cutoff=30)
    grid = np.linspace(-5.0, 5.0, 101)
    wigner = iq.phase_space.wigner_function(cat_state, grid, grid)

    source = iqc.BinaryCoherentSource(mu_0=2.0, mu_1=8.0)
    channel = iqc.FiberChannel(attenuation_db_per_km=0.2)
    state_0 = channel.propagate(
        mu=source.mean_photon_number(0),
        alpha=source.amplitude(0),
        distance_km=20.0,
    )
    state_1 = channel.propagate(
        mu=source.mean_photon_number(1),
        alpha=source.amplitude(1),
        distance_km=20.0,
    )
    receiver = iqc.ErasurePNRReceiver(
        lower_threshold=1,
        upper_threshold=3,
    )
    metrics = receiver.analytical_metrics(state_0, state_1)

    print(f"iQuant4 alpha version: {iq.__version__}")
    print(f"Cat-state mean photons: {iq.metrics.mean_photon_number(cat_state):.6f}")
    print(
        "Wigner normalization: "
        f"{iq.phase_space.wigner_normalization(wigner, grid, grid):.6f}"
    )
    print(f"20 km PNR acceptance: {metrics.acceptance_probability:.6f}")
    print(f"20 km PNR conditional BER: {metrics.conditional_ber:.6f}")


if __name__ == "__main__":
    main()
