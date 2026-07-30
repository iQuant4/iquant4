from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.axes import Axes
from matplotlib.figure import Figure
from numpy.typing import NDArray

from iqcore.states import (
    QuantumStateArray,
    density_matrix,
)




def wigner_function(
    state: QuantumStateArray,
    x_values: NDArray[np.float64],
    p_values: NDArray[np.float64],
) -> NDArray[np.float64]:
    """
    Compute the single-mode Wigner function in the Fock basis.

    The quadrature convention is

        x = (a + a†) / sqrt(2)
        p = (a - a†) / (i sqrt(2)),

    so that

        [x, p] = i.

    With this convention, the vacuum Wigner function is

        W(x, p) = exp[-(x^2 + p^2)] / pi.

    Parameters
    ----------
    state:
        Single-mode state vector or density matrix.

    x_values:
        One-dimensional array of position-quadrature values.

    p_values:
        One-dimensional array of momentum-quadrature values.

    Returns
    -------
    numpy.ndarray
        Two-dimensional Wigner-function array with shape

            (len(p_values), len(x_values)).

        The first index corresponds to p and the second to x.
    """
    rho = density_matrix(state)

    x_array = np.asarray(
        x_values,
        dtype=np.float64,
    )

    p_array = np.asarray(
        p_values,
        dtype=np.float64,
    )

    if x_array.ndim != 1:
        raise ValueError(
            "x_values must be one-dimensional."
        )

    if p_array.ndim != 1:
        raise ValueError(
            "p_values must be one-dimensional."
        )

    if x_array.size < 2:
        raise ValueError(
            "x_values must contain at least two points."
        )

    if p_array.size < 2:
        raise ValueError(
            "p_values must contain at least two points."
        )

    x_grid, p_grid = np.meshgrid(
        x_array,
        p_array,
        indexing="xy",
    )

    phase_space_amplitude = (
        x_grid + 1j * p_grid
    ) / np.sqrt(2.0)

    cutoff = rho.shape[0]

    basis_functions: list[
        NDArray[np.complex128]
    ] = [
        np.zeros_like(
            phase_space_amplitude,
            dtype=np.complex128,
        )
        for _ in range(cutoff)
    ]

    basis_functions[0] = (
        np.exp(
            -2.0
            * np.abs(
                phase_space_amplitude
            ) ** 2
        )
        / np.pi
    ).astype(np.complex128)

    wigner = (
        np.real(rho[0, 0])
        * np.real(basis_functions[0])
    )

    # Construct W_{0,n}.
    for n in range(1, cutoff):
        basis_functions[n] = (
            2.0
            * phase_space_amplitude
            * basis_functions[n - 1]
            / np.sqrt(n)
        )

        wigner += (
            2.0
            * np.real(
                rho[0, n]
                * basis_functions[n]
            )
        )

    # Construct W_{m,n} recursively.
    for m in range(1, cutoff):
        previous_mn = (
            basis_functions[m].copy()
        )

        basis_functions[m] = (
            2.0
            * np.conjugate(
                phase_space_amplitude
            )
            * previous_mn
            - np.sqrt(m)
            * basis_functions[m - 1]
        ) / np.sqrt(m)

        wigner += (
            np.real(rho[m, m])
            * np.real(
                basis_functions[m]
            )
        )

        for n in range(m + 1, cutoff):
            old_basis_function = (
                basis_functions[n].copy()
            )

            basis_functions[n] = (
                2.0
                * phase_space_amplitude
                * basis_functions[n - 1]
                - np.sqrt(m)
                * previous_mn
            ) / np.sqrt(n)

            previous_mn = (
                old_basis_function
            )

            wigner += (
                2.0
                * np.real(
                    rho[m, n]
                    * basis_functions[n]
                )
            )

    numerical_tolerance = 1e-14

    wigner[
        np.abs(wigner)
        < numerical_tolerance
    ] = 0.0

    return np.asarray(
        wigner,
        dtype=np.float64,
    )


def wigner_normalization(
    wigner: NDArray[np.float64],
    x_values: NDArray[np.float64],
    p_values: NDArray[np.float64],
) -> float:
    """
    Numerically evaluate the phase-space integral of W(x, p).

    For a normalized state and a sufficiently large grid,

        integral W(x, p) dx dp = 1.
    """
    wigner_array = np.asarray(
        wigner,
        dtype=np.float64,
    )

    x_array = np.asarray(
        x_values,
        dtype=np.float64,
    )

    p_array = np.asarray(
        p_values,
        dtype=np.float64,
    )

    expected_shape = (
        p_array.size,
        x_array.size,
    )

    if wigner_array.shape != expected_shape:
        raise ValueError(
            "Wigner array shape must be "
            "(len(p_values), len(x_values))."
        )

    integral_over_x = np.trapezoid(
        wigner_array,
        x=x_array,
        axis=1,
    )

    integral = np.trapezoid(
        integral_over_x,
        x=p_array,
    )

    return float(integral)


def wigner_negativity(
    wigner: NDArray[np.float64],
    x_values: NDArray[np.float64],
    p_values: NDArray[np.float64],
) -> float:
    """
    Calculate the integrated Wigner negativity.

    The definition used is

        N_W = 1/2 [integral |W| dx dp - 1].

    A nonnegative Gaussian state ideally has zero Wigner
    negativity. Nonclassical states such as cat states may
    have positive negativity.
    """
    wigner_array = np.asarray(
        wigner,
        dtype=np.float64,
    )

    x_array = np.asarray(
        x_values,
        dtype=np.float64,
    )

    p_array = np.asarray(
        p_values,
        dtype=np.float64,
    )

    absolute_integral_over_x = np.trapezoid(
        np.abs(wigner_array),
        x=x_array,
        axis=1,
    )

    absolute_integral = np.trapezoid(
        absolute_integral_over_x,
        x=p_array,
    )

    normalization = wigner_normalization(
        wigner=wigner_array,
        x_values=x_array,
        p_values=p_array,
    )

    negativity = 0.5 * (
        absolute_integral
        - normalization
    )

    return float(
        max(negativity, 0.0)
    )


def plot_wigner(
    state: QuantumStateArray,
    *,
    x_values: NDArray[np.float64] | None = None,
    p_values: NDArray[np.float64] | None = None,
    extent: float = 5.0,
    number_of_points: int = 201,
    title: str = "Wigner function",
    ax: Axes | None = None,
    show: bool = True,
    display_colorbar: bool = True,
) -> tuple[
    Figure,
    Axes,
    NDArray[np.float64],
]:
    """
    Compute and plot a single-mode Wigner function.

    Parameters
    ----------
    state:
        State vector or density matrix.

    x_values, p_values:
        Optional phase-space grids. When omitted, uniform
        grids from -extent to +extent are generated.

    extent:
        Default absolute quadrature limit.

    number_of_points:
        Number of points along each default grid.

    title:
        Figure title.

    ax:
        Existing Matplotlib axes.

    show:
        Call ``plt.show()`` when True.

    display_colorbar:
        Add a colorbar when True.

    Returns
    -------
    tuple
        Figure, axes, and computed Wigner-function array.
    """
    if extent <= 0.0:
        raise ValueError(
            "Extent must be positive."
        )

    if number_of_points < 2:
        raise ValueError(
            "number_of_points must be at least 2."
        )

    if x_values is None:
        x_array = np.linspace(
            -extent,
            extent,
            number_of_points,
            dtype=np.float64,
        )
    else:
        x_array = np.asarray(
            x_values,
            dtype=np.float64,
        )

    if p_values is None:
        p_array = np.linspace(
            -extent,
            extent,
            number_of_points,
            dtype=np.float64,
        )
    else:
        p_array = np.asarray(
            p_values,
            dtype=np.float64,
        )

    wigner = wigner_function(
        state=state,
        x_values=x_array,
        p_values=p_array,
    )

    if ax is None:
        figure, axes = plt.subplots(
            figsize=(6.6, 5.6)
        )
    else:
        axes = ax
        figure = axes.figure

    maximum_absolute_value = float(
        np.max(np.abs(wigner))
    )

    if np.isclose(
        maximum_absolute_value,
        0.0,
    ):
        maximum_absolute_value = 1.0

    image = axes.imshow(
        wigner,
        origin="lower",
        extent=[
            x_array[0],
            x_array[-1],
            p_array[0],
            p_array[-1],
        ],
        aspect="equal",
        interpolation="bilinear",
        cmap="RdBu_r",
        vmin=-maximum_absolute_value,
        vmax=maximum_absolute_value,
    )

    axes.contour(
        x_array,
        p_array,
        wigner,
        levels=12,
        linewidths=0.6,
        alpha=0.65,
    )

    axes.axhline(
        0.0,
        linewidth=0.6,
        alpha=0.4,
    )
    axes.axvline(
        0.0,
        linewidth=0.6,
        alpha=0.4,
    )

    axes.set_xlabel(
        r"Position quadrature, $x$"
    )
    axes.set_ylabel(
        r"Momentum quadrature, $p$"
    )
    axes.set_title(title)

    if display_colorbar:
        colorbar = figure.colorbar(
            image,
            ax=axes,
        )
        colorbar.set_label(
            r"$W(x,p)$"
        )

    figure.tight_layout()

    if show:
        plt.show()

    return figure, axes, wigner