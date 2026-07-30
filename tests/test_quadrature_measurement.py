import numpy as np
import pytest

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


CUTOFF = 40
X_VALUES = np.linspace(
    -7.0,
    7.0,
    4001,
)


def test_position_quadrature_is_hermitian() -> None:
    position = position_quadrature_operator(
        cutoff=CUTOFF
    )

    error = np.linalg.norm(
        position
        - position.conjugate().T
    )

    assert error < 1e-12


def test_momentum_quadrature_is_hermitian() -> None:
    momentum = momentum_quadrature_operator(
        cutoff=CUTOFF
    )

    error = np.linalg.norm(
        momentum
        - momentum.conjugate().T
    )

    assert error < 1e-12


def test_vacuum_quadrature_statistics() -> None:
    vacuum = fock_state(
        photon_number=0,
        cutoff=CUTOFF,
    )

    statistics = quadrature_statistics(
        vacuum,
        angle=0.0,
    )

    assert statistics.mean == pytest.approx(
        0.0,
        abs=1e-12,
    )

    assert statistics.variance == pytest.approx(
        0.5,
        abs=1e-12,
    )

    assert statistics.standard_deviation == pytest.approx(
        np.sqrt(0.5),
        abs=1e-12,
    )


def test_vacuum_probability_density() -> None:
    vacuum = fock_state(
        photon_number=0,
        cutoff=CUTOFF,
    )

    probability_density = (
        quadrature_probability_density(
            vacuum,
            X_VALUES,
            angle=0.0,
        )
    )

    normalization = (
        quadrature_distribution_normalization(
            X_VALUES,
            probability_density,
        )
    )

    mean, variance = distribution_statistics(
        X_VALUES,
        probability_density,
    )

    assert normalization == pytest.approx(
        1.0,
        abs=1e-10,
    )

    assert mean == pytest.approx(
        0.0,
        abs=1e-10,
    )

    assert variance == pytest.approx(
        0.5,
        abs=1e-9,
    )


@pytest.mark.parametrize(
    "angle",
    [
        0.0,
        np.pi / 2.0,
        np.pi / 4.0,
    ],
)
def test_coherent_state_operator_statistics(
    angle: float,
) -> None:
    alpha = 1.5 + 0.6j

    coherent = coherent_state(
        alpha=alpha,
        cutoff=CUTOFF,
    )

    numerical = quadrature_statistics(
        coherent,
        angle=angle,
    )

    analytical_mean, analytical_variance = (
        coherent_quadrature_parameters(
            alpha=alpha,
            angle=angle,
        )
    )

    assert numerical.mean == pytest.approx(
        analytical_mean,
        abs=1e-10,
    )

    assert numerical.variance == pytest.approx(
        analytical_variance,
        abs=1e-10,
    )


@pytest.mark.parametrize(
    "angle",
    [
        0.0,
        np.pi / 2.0,
        np.pi / 4.0,
    ],
)
def test_coherent_state_grid_statistics(
    angle: float,
) -> None:
    alpha = 1.5 + 0.6j

    coherent = coherent_state(
        alpha=alpha,
        cutoff=CUTOFF,
    )

    probability_density = (
        quadrature_probability_density(
            coherent,
            X_VALUES,
            angle=angle,
        )
    )

    grid_mean, grid_variance = (
        distribution_statistics(
            X_VALUES,
            probability_density,
        )
    )

    analytical_mean, analytical_variance = (
        coherent_quadrature_parameters(
            alpha=alpha,
            angle=angle,
        )
    )

    assert grid_mean == pytest.approx(
        analytical_mean,
        abs=1e-8,
    )

    assert grid_variance == pytest.approx(
        analytical_variance,
        abs=1e-8,
    )


def test_squeezed_vacuum_variances() -> None:
    squeezing_parameter = 0.7

    # Positional arguments avoid dependence on the exact name
    # used for the squeezing-strength parameter.
    squeezed = squeezed_vacuum_state(
        squeezing_parameter,
        0.0,
        CUTOFF,
    )

    x_statistics = quadrature_statistics(
        squeezed,
        angle=0.0,
    )

    p_statistics = quadrature_statistics(
        squeezed,
        angle=np.pi / 2.0,
    )

    expected_x_variance = (
        0.5
        * np.exp(
            -2.0 * squeezing_parameter
        )
    )

    expected_p_variance = (
        0.5
        * np.exp(
            2.0 * squeezing_parameter
        )
    )

    assert x_statistics.variance == pytest.approx(
        expected_x_variance,
        rel=1e-6,
        abs=1e-8,
    )

    assert p_statistics.variance == pytest.approx(
        expected_p_variance,
        rel=1e-6,
        abs=1e-8,
    )


def test_thermal_state_quadrature_variance() -> None:
    mean_photon_number = 1.2

    thermal = thermal_state(
        mean_photon_number=mean_photon_number,
        cutoff=CUTOFF,
    )

    statistics = quadrature_statistics(
        thermal,
        angle=0.0,
    )

    expected_variance = (
        mean_photon_number + 0.5
    )

    assert statistics.mean == pytest.approx(
        0.0,
        abs=1e-12,
    )

    assert statistics.variance == pytest.approx(
        expected_variance,
        rel=1e-6,
        abs=1e-8,
    )


def test_quadrature_sampling_matches_coherent_state() -> None:
    alpha = 1.5 + 0.6j

    coherent = coherent_state(
        alpha=alpha,
        cutoff=CUTOFF,
    )

    samples = sample_quadrature(
        coherent,
        number_of_samples=20_000,
        angle=0.0,
        x_min=-7.0,
        x_max=7.0,
        number_of_grid_points=4001,
        seed=7,
    )

    expected_mean, expected_variance = (
        coherent_quadrature_parameters(
            alpha=alpha,
            angle=0.0,
        )
    )

    assert samples.shape == (20_000,)

    assert np.mean(samples) == pytest.approx(
        expected_mean,
        abs=0.025,
    )

    assert np.var(samples) == pytest.approx(
        expected_variance,
        abs=0.025,
    )


def test_invalid_quadrature_grid_raises_error() -> None:
    vacuum = fock_state(
        photon_number=0,
        cutoff=10,
    )

    invalid_grid = np.array(
        [
            -1.0,
            0.0,
            0.0,
            1.0,
        ]
    )

    with pytest.raises(
        ValueError,
        match="strictly increasing",
    ):
        quadrature_probability_density(
            vacuum,
            invalid_grid,
        )


def test_invalid_sampling_arguments_raise_error() -> None:
    vacuum = fock_state(
        photon_number=0,
        cutoff=10,
    )

    with pytest.raises(
        ValueError,
        match="Number of samples",
    ):
        sample_quadrature(
            vacuum,
            number_of_samples=0,
        )

    with pytest.raises(
        ValueError,
        match="x_max",
    ):
        sample_quadrature(
            vacuum,
            number_of_samples=100,
            x_min=1.0,
            x_max=-1.0,
        )
def test_iquant4comm_measurement_public_api() -> None:
    from iq4comm.measurements import (
        quadrature_probability_density,
        quadrature_statistics,
        sample_quadrature,
    )

    assert callable(quadrature_probability_density)
    assert callable(quadrature_statistics)
    assert callable(sample_quadrature)

def test_iquant4comm_bosonic_operator_public_api() -> None:
    from iq4comm.operators import (
        annihilation_operator,
        displacement_operator,
        squeezing_operator,
    )

    assert callable(annihilation_operator)
    assert callable(displacement_operator)
    assert callable(squeezing_operator)
