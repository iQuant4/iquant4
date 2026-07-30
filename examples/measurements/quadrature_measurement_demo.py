import numpy as np

from iqcore.measurements import (
    coherent_quadrature_parameters,
    distribution_statistics,
    momentum_quadrature_operator,
    position_quadrature_operator,
    quadrature_distribution_normalization,
    quadrature_probability_density,
    quadrature_statistics,
    sample_quadrature,
)
from iqcore.states import (
    coherent_state,
    fock_state,
    squeezed_vacuum_state,
    thermal_state,
)


cutoff = 40

x_values = np.linspace(
    -7.0,
    7.0,
    4001,
)


print("Quadrature operators")
print("--------------------")

position = position_quadrature_operator(
    cutoff=cutoff
)

momentum = momentum_quadrature_operator(
    cutoff=cutoff
)

print(
    "Position Hermiticity error:",
    np.linalg.norm(
        position
        - position.conjugate().T
    ),
)

print(
    "Momentum Hermiticity error:",
    np.linalg.norm(
        momentum
        - momentum.conjugate().T
    ),
)


print()
print("Vacuum state")
print("------------")

vacuum = fock_state(
    photon_number=0,
    cutoff=cutoff,
)

vacuum_statistics = quadrature_statistics(
    vacuum,
    angle=0.0,
)

vacuum_density = quadrature_probability_density(
    vacuum,
    x_values,
    angle=0.0,
)

vacuum_grid_mean, vacuum_grid_variance = (
    distribution_statistics(
        x_values,
        vacuum_density,
    )
)

print(
    "Operator mean:",
    vacuum_statistics.mean,
)

print(
    "Operator variance:",
    vacuum_statistics.variance,
)

print(
    "Grid normalization:",
    quadrature_distribution_normalization(
        x_values,
        vacuum_density,
    ),
)

print(
    "Grid mean:",
    vacuum_grid_mean,
)

print(
    "Grid variance:",
    vacuum_grid_variance,
)


print()
print("Coherent state")
print("--------------")

alpha = 1.5 + 0.6j

coherent = coherent_state(
    alpha=alpha,
    cutoff=cutoff,
)

for angle in (
    0.0,
    np.pi / 2.0,
    np.pi / 4.0,
):
    numerical_statistics = (
        quadrature_statistics(
            coherent,
            angle=angle,
        )
    )

    analytical_mean, analytical_variance = (
        coherent_quadrature_parameters(
            alpha=alpha,
            angle=angle,
        )
    )

    coherent_density = (
        quadrature_probability_density(
            coherent,
            x_values,
            angle=angle,
        )
    )

    grid_mean, grid_variance = (
        distribution_statistics(
            x_values,
            coherent_density,
        )
    )

    print()
    print(
        "Angle:",
        angle,
    )

    print(
        "Operator mean:",
        numerical_statistics.mean,
    )

    print(
        "Analytical mean:",
        analytical_mean,
    )

    print(
        "Grid mean:",
        grid_mean,
    )

    print(
        "Operator variance:",
        numerical_statistics.variance,
    )

    print(
        "Analytical variance:",
        analytical_variance,
    )

    print(
        "Grid variance:",
        grid_variance,
    )


print()
print("Squeezed vacuum")
print("----------------")

squeezing_parameter = 0.7

squeezed = squeezed_vacuum_state(
    squeezing_magnitude=squeezing_parameter,
    squeezing_phase=0.0,
    cutoff=cutoff,
)

squeezed_x = quadrature_statistics(
    squeezed,
    angle=0.0,
)

squeezed_p = quadrature_statistics(
    squeezed,
    angle=np.pi / 2.0,
)

print(
    "X variance:",
    squeezed_x.variance,
)

print(
    "Expected X variance:",
    0.5 * np.exp(
        -2.0 * squeezing_parameter
    ),
)

print(
    "P variance:",
    squeezed_p.variance,
)

print(
    "Expected P variance:",
    0.5 * np.exp(
        2.0 * squeezing_parameter
    ),
)


print()
print("Thermal state")
print("-------------")

thermal_mean_photons = 1.2

thermal = thermal_state(
    mean_photon_number=thermal_mean_photons,
    cutoff=cutoff,
)

thermal_statistics = quadrature_statistics(
    thermal,
    angle=0.0,
)

print(
    "Quadrature mean:",
    thermal_statistics.mean,
)

print(
    "Quadrature variance:",
    thermal_statistics.variance,
)

print(
    "Expected variance:",
    thermal_mean_photons + 0.5,
)


print()
print("Numerical homodyne sampling")
print("---------------------------")

samples = sample_quadrature(
    coherent,
    number_of_samples=100_000,
    angle=0.0,
    x_min=-7.0,
    x_max=7.0,
    number_of_grid_points=4001,
    seed=7,
)

expected_sample_mean, expected_sample_variance = (
    coherent_quadrature_parameters(
        alpha=alpha,
        angle=0.0,
    )
)

print(
    "Sample mean:",
    np.mean(samples),
)

print(
    "Expected mean:",
    expected_sample_mean,
)

print(
    "Sample variance:",
    np.var(samples),
)

print(
    "Expected variance:",
    expected_sample_variance,
)