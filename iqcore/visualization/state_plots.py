from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.axes import Axes
from matplotlib.figure import Figure

from iqcore.metrics import (
    mean_photon_number,
    photon_number_distribution,
    photon_number_variance,
    state_purity,
)
from iqcore.states import (
    QuantumStateArray,
    density_matrix,
)

def plot_fock_distribution(
    state: QuantumStateArray,
    *,
    maximum_photon_number: int | None = None,
    title: str = "Photon-number distribution",
    ax: Axes | None = None,
    show: bool = True,
) -> tuple[Figure, Axes]:
    """
    Plot the photon-number distribution.

    Parameters
    ----------
    state:
        State vector or density matrix.

    maximum_photon_number:
        Largest photon number to display. By default, all
        available photon numbers are displayed.

    title:
        Plot title.

    ax:
        Existing Matplotlib axes. A new figure is created
        when omitted.

    show:
        Call ``plt.show()`` when True.

    Returns
    -------
    tuple
        Matplotlib figure and axes.
    """
    probabilities = photon_number_distribution(
        state
    )

    dimension = probabilities.size

    if maximum_photon_number is None:
        displayed_dimension = dimension
    else:
        if maximum_photon_number < 0:
            raise ValueError(
                "Maximum photon number cannot be negative."
            )

        displayed_dimension = min(
            maximum_photon_number + 1,
            dimension,
        )

    photon_numbers = np.arange(
        displayed_dimension,
        dtype=np.int64,
    )

    displayed_probabilities = probabilities[
        :displayed_dimension
    ]

    if ax is None:
        figure, axes = plt.subplots(
            figsize=(8.0, 4.8)
        )
    else:
        axes = ax
        figure = axes.figure

    axes.bar(
        photon_numbers,
        displayed_probabilities,
        width=0.8,
        edgecolor="black",
        linewidth=0.7,
    )

    axes.set_xlabel(
        r"Photon number, $n$"
    )

    axes.set_ylabel(
        r"Probability, $P(n)$"
    )

    axes.set_title(title)

    if displayed_dimension <= 25:
        axes.set_xticks(
            photon_numbers
        )

    maximum_probability = float(
        np.max(displayed_probabilities)
    )

    upper_limit = (
        1.1 * maximum_probability
        if maximum_probability > 0.0
        else 1.0
    )

    axes.set_ylim(
        0.0,
        upper_limit,
    )

    axes.set_xlim(
        -0.6,
        displayed_dimension - 0.4,
    )

    axes.grid(
        axis="y",
        alpha=0.25,
    )

    figure.tight_layout()

    if show:
        plt.show()

    return figure, axes

def plot_density_matrix(
    state: QuantumStateArray,
    *,
    component: str = "magnitude",
    title: str | None = None,
    maximum_index: int | None = None,
    ax: Axes | None = None,
    show: bool = True,
    display_colorbar: bool = True,
) -> tuple[Figure, Axes]:
    """
    Plot a density matrix.

    Parameters
    ----------
    state:
        State vector or density matrix.

    component:
        Quantity to display. Supported values are:

        - ``"magnitude"``
        - ``"real"``
        - ``"imaginary"``
        - ``"phase"``

    title:
        Optional plot title.

    maximum_index:
        Largest Fock index to display. By default, the full
        density matrix is displayed.

    ax:
        Existing Matplotlib axes.

    show:
        Call ``plt.show()`` when True.

    display_colorbar:
        Add a colorbar when True.

    Returns
    -------
    tuple
        Matplotlib figure and axes.
    """
    rho = density_matrix(state)

    if maximum_index is not None:
        if maximum_index < 0:
            raise ValueError(
                "Maximum index cannot be negative."
            )

        displayed_dimension = min(
            maximum_index + 1,
            rho.shape[0],
        )

        rho = rho[
            :displayed_dimension,
            :displayed_dimension,
        ]

    normalized_component = (
        component.strip().lower()
    )

    if normalized_component == "magnitude":
        matrix_to_plot = np.abs(rho)

        default_title = (
            "Density-matrix magnitude"
        )

        colorbar_label = (
            r"$|\rho_{mn}|$"
        )

        color_map = "viridis"

        minimum_value = 0.0

        maximum_value = float(
            np.max(matrix_to_plot)
        )

    elif normalized_component == "real":
        matrix_to_plot = np.real(rho)

        default_title = (
            "Real part of density matrix"
        )

        colorbar_label = (
            r"$\mathrm{Re}(\rho_{mn})$"
        )

        color_map = "RdBu_r"

        maximum_absolute_value = float(
            np.max(
                np.abs(matrix_to_plot)
            )
        )

        if np.isclose(
            maximum_absolute_value,
            0.0,
        ):
            maximum_absolute_value = 1.0

        minimum_value = (
            -maximum_absolute_value
        )

        maximum_value = (
            maximum_absolute_value
        )

    elif normalized_component == "imaginary":
        matrix_to_plot = np.imag(rho)

        default_title = (
            "Imaginary part of density matrix"
        )

        colorbar_label = (
            r"$\mathrm{Im}(\rho_{mn})$"
        )

        color_map = "RdBu_r"

        maximum_absolute_value = float(
            np.max(
                np.abs(matrix_to_plot)
            )
        )

        if np.isclose(
            maximum_absolute_value,
            0.0,
        ):
            maximum_absolute_value = 1.0

        minimum_value = (
            -maximum_absolute_value
        )

        maximum_value = (
            maximum_absolute_value
        )

    elif normalized_component == "phase":
        matrix_to_plot = np.angle(rho)

        default_title = (
            "Density-matrix phase"
        )

        colorbar_label = (
            r"$\arg(\rho_{mn})$"
        )

        color_map = "twilight"

        minimum_value = -np.pi

        maximum_value = np.pi

    else:
        raise ValueError(
            "Component must be 'magnitude', 'real', "
            "'imaginary', or 'phase'."
        )

    if ax is None:
        figure, axes = plt.subplots(
            figsize=(6.4, 5.4)
        )
    else:
        axes = ax
        figure = axes.figure

    image = axes.imshow(
        matrix_to_plot,
        origin="lower",
        aspect="equal",
        interpolation="nearest",
        cmap=color_map,
        vmin=minimum_value,
        vmax=maximum_value,
    )

    axes.set_xlabel(
        r"Fock index, $n$"
    )

    axes.set_ylabel(
        r"Fock index, $m$"
    )

    axes.set_title(
        title or default_title
    )

    if display_colorbar:
        colorbar = figure.colorbar(
            image,
            ax=axes,
        )

        colorbar.set_label(
            colorbar_label
        )

    figure.tight_layout()

    if show:
        plt.show()

    return figure, axes

def print_state_summary(
    state: QuantumStateArray,
    *,
    name: str = "Quantum state",
) -> None:
    """
    Print basic quantum-state diagnostics.

    Parameters
    ----------
    state:
        State vector or density matrix.

    name:
        State name displayed in the summary.
    """
    rho = density_matrix(state)

    trace = np.trace(rho)

    state_purity_value = state_purity(
        state
    )

    mean_value = mean_photon_number(
        state
    )

    variance_value = photon_number_variance(
        state
    )

    print(name)

    print(
        "-" * len(name)
    )

    print(
        f"Dimension: {rho.shape[0]}"
    )

    print(
        f"Trace: {trace}"
    )

    print(
        "Purity: "
        f"{state_purity_value:.8f}"
    )

    print(
        "Mean photon number: "
        f"{mean_value:.8f}"
    )

    print(
        "Photon-number variance: "
        f"{variance_value:.8f}"
    )

def plot_state_summary(
    state: QuantumStateArray,
    *,
    name: str = "Quantum state",
    maximum_photon_number: int | None = None,
    density_matrix_component: str = "magnitude",
    show: bool = True,
) -> tuple[
    Figure,
    tuple[Axes, Axes],
]:
    """
    Plot a photon-number distribution and density matrix in
    one summary figure.

    Parameters
    ----------
    state:
        State vector or density matrix.

    name:
        State name used in the figure title.

    maximum_photon_number:
        Largest photon number displayed in the probability
        plot.

    density_matrix_component:
        Density-matrix component displayed in the second
        panel.

    show:
        Call ``plt.show()`` when True.

    Returns
    -------
    tuple
        Figure and a tuple containing the two axes.
    """
    figure, axes_array = plt.subplots(
        nrows=1,
        ncols=2,
        figsize=(12.0, 4.8),
    )

    fock_axes = axes_array[0]

    density_axes = axes_array[1]

    plot_fock_distribution(
        state,
        maximum_photon_number=(
            maximum_photon_number
        ),
        title=(
            f"{name}: photon-number distribution"
        ),
        ax=fock_axes,
        show=False,
    )

    plot_density_matrix(
        state,
        component=(
            density_matrix_component
        ),
        title=(
            f"{name}: density matrix"
        ),
        maximum_index=(
            maximum_photon_number
        ),
        ax=density_axes,
        show=False,
        display_colorbar=True,
    )

    figure.suptitle(
        name,
        fontsize=14,
    )

    figure.tight_layout()

    if show:
        plt.show()

    return (
        figure,
        (
            fock_axes,
            density_axes,
        ),
    )

__all__ = [
    "plot_density_matrix",
    "plot_fock_distribution",
    "plot_state_summary",
    "print_state_summary",
]
