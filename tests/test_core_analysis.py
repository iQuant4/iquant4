from __future__ import annotations

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pytest

from iqcore.metrics import (
    mean_photon_number,
    photon_number_distribution,
    photon_number_variance,
    state_purity,
)
from iqcore.phase_space import (
    wigner_function,
    wigner_negativity,
    wigner_normalization,
)
from iqcore.states import (
    coherent_state,
    even_cat_state,
    fock_state,
    thermal_state,
)
from iqcore.visualization import (
    plot_density_matrix,
    plot_fock_distribution,
    plot_state_summary,
)


def test_coherent_photon_statistics() -> None:
    alpha = 1.2 - 0.4j
    state = coherent_state(alpha=alpha, cutoff=35)
    probabilities = photon_number_distribution(state)

    assert np.sum(probabilities) == pytest.approx(1.0)
    assert mean_photon_number(state) == pytest.approx(
        abs(alpha) ** 2,
        rel=1e-11,
    )
    assert photon_number_variance(state) == pytest.approx(
        abs(alpha) ** 2,
        rel=1e-10,
    )
    assert state_purity(state) == pytest.approx(1.0)


def test_fock_photon_statistics() -> None:
    state = fock_state(photon_number=4, cutoff=10)

    assert mean_photon_number(state) == pytest.approx(4.0)
    assert photon_number_variance(state) == pytest.approx(0.0)
    assert photon_number_distribution(state)[4] == pytest.approx(1.0)


def test_thermal_photon_statistics() -> None:
    mean = 1.2
    state = thermal_state(mean_photon_number=mean, cutoff=50)

    assert mean_photon_number(state) == pytest.approx(
        mean,
        abs=1e-8,
    )
    assert state_purity(state) == pytest.approx(
        1.0 / (2.0 * mean + 1.0),
        abs=1e-9,
    )


def test_vacuum_wigner_normalization_and_positivity() -> None:
    grid = np.linspace(-5.0, 5.0, 121)
    wigner = wigner_function(
        fock_state(photon_number=0, cutoff=12),
        grid,
        grid,
    )

    assert wigner.shape == (121, 121)
    assert wigner_normalization(wigner, grid, grid) == pytest.approx(
        1.0,
        abs=1e-6,
    )
    assert wigner_negativity(wigner, grid, grid) == pytest.approx(
        0.0,
        abs=1e-12,
    )


def test_even_cat_has_wigner_negativity() -> None:
    grid = np.linspace(-5.0, 5.0, 121)
    state = even_cat_state(alpha=1.5, cutoff=30)
    wigner = wigner_function(state, grid, grid)

    assert wigner_negativity(wigner, grid, grid) > 0.15


def test_wigner_shape_validation() -> None:
    grid = np.linspace(-2.0, 2.0, 11)

    with pytest.raises(ValueError, match="Wigner array shape"):
        wigner_normalization(
            np.zeros((5, 5)),
            grid,
            grid,
        )


def test_plot_fock_distribution_returns_matplotlib_objects() -> None:
    figure, axes = plot_fock_distribution(
        fock_state(photon_number=2, cutoff=8),
        show=False,
    )

    assert axes.figure is figure
    assert len(axes.patches) == 8
    plt.close(figure)


@pytest.mark.parametrize(
    "component",
    ["magnitude", "real", "imaginary", "phase"],
)
def test_plot_density_matrix_components(component: str) -> None:
    figure, axes = plot_density_matrix(
        coherent_state(alpha=0.7 + 0.2j, cutoff=12),
        component=component,
        show=False,
    )

    assert axes.figure is figure
    assert len(axes.images) == 1
    plt.close(figure)


def test_plot_state_summary_returns_two_primary_axes() -> None:
    figure, axes = plot_state_summary(
        thermal_state(mean_photon_number=0.5, cutoff=12),
        name="Thermal state",
        maximum_photon_number=8,
        show=False,
    )

    assert len(axes) == 2
    assert axes[0].figure is figure
    assert axes[1].figure is figure
    plt.close(figure)


def test_invalid_plot_arguments_raise() -> None:
    state = fock_state(photon_number=0, cutoff=5)

    with pytest.raises(ValueError, match="Maximum photon number"):
        plot_fock_distribution(
            state,
            maximum_photon_number=-1,
            show=False,
        )

    with pytest.raises(ValueError, match="Component must be"):
        plot_density_matrix(
            state,
            component="unsupported",
            show=False,
        )


def test_legacy_and_communication_visualization_apis() -> None:
    from iq4comm.visualization import (
        plot_fock_distribution as communication_plot,
    )
    from visualization import (
        mean_photon_number as legacy_mean,
        plot_fock_distribution as legacy_plot,
    )

    assert communication_plot is plot_fock_distribution
    assert legacy_plot is plot_fock_distribution
    assert legacy_mean is mean_photon_number
