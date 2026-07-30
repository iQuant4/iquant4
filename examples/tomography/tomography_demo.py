from __future__ import annotations

import numpy as np
import matplotlib.pyplot as plt

from iqcore.optics import SignFreeOPA
from iqcore.measurements.homodyne_sampling import (
    quadrature_probability_density,
    sample_from_density,
)
from iqcore.states import fock_state


def main() -> None:
    cutoff = 20
    photon_number = 1

    phase = 0.0
    sample_count = 50_000
    seed = 7

    x_values = np.linspace(
        -5.0,
        5.0,
        4001,
    )

    state = fock_state(
        photon_number=photon_number,
        cutoff=cutoff,
    )

    density = quadrature_probability_density(
        state=state,
        x_values=x_values,
        phase=phase,
    )

    rng = np.random.default_rng(seed)

    homodyne_samples = sample_from_density(
        x_values=x_values,
        probability_density=density,
        sample_count=sample_count,
        rng=rng,
    )

    opa = SignFreeOPA(
        gain_parameter=np.log(10.0) / 2.0,
        phase=phase,
    )

    power_samples = opa.measure_power(
        quadrature_samples=homodyne_samples,
    )

    sign_free_samples = (
        opa.recover_sign_free_quadrature(
            power_samples=power_samples,
        )
    )

    print("iQuant4 OPA Sign-Free Measurement")
    print("--------------------------------")
    print(f"State              : |{photon_number}>")
    print(f"Fock cutoff        : {cutoff}")
    print(f"Phase              : {phase:.3f} rad")
    print(f"Sample count       : {sample_count}")
    print(f"OPA power gain     : {opa.power_gain:.3f}")
    print(f"OPA gain           : {opa.gain_db:.3f} dB")
    print()

    print(
        "Mean homodyne x   : "
        f"{np.mean(homodyne_samples):.6f}"
    )

    print(
        "Mean sign-free |x|: "
        f"{np.mean(sign_free_samples):.6f}"
    )

    print(
        "Minimum |x|       : "
        f"{np.min(sign_free_samples):.6f}"
    )

    print(
        "Maximum |x|       : "
        f"{np.max(sign_free_samples):.6f}"
    )

    plt.figure(figsize=(8, 5))

    plt.hist(
        homodyne_samples,
        bins=100,
        density=True,
        alpha=0.65,
        label=r"Homodyne $x_\phi$",
    )

    plt.plot(
        x_values,
        density,
        linewidth=2.0,
        label=r"Theoretical $P(x_\phi)$",
    )

    plt.xlabel(r"$x_\phi$")
    plt.ylabel("Probability density")
    plt.title("Ordinary Homodyne Measurement")
    plt.legend()
    plt.tight_layout()
    plt.show()

    plt.figure(figsize=(8, 5))

    plt.hist(
        sign_free_samples,
        bins=100,
        density=True,
        alpha=0.75,
        label=r"OPA sign-free $|x_\phi|$",
    )

    plt.xlabel(r"$|x_\phi|$")
    plt.ylabel("Probability density")
    plt.title(
        "Ideal OPA Quadrature-Power Measurement"
    )
    plt.legend()
    plt.tight_layout()
    plt.show()


if __name__ == "__main__":
    main()