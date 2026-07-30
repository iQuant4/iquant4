import matplotlib.pyplot as plt
import numpy as np

from iqcore.phase_space import (
    plot_wigner,
    wigner_negativity,
    wigner_normalization,
)
from iqcore.states import (
    coherent_state,
    even_cat_state,
    squeezed_vacuum_state,
    thermal_state,
)


cutoff = 30

x_values = np.linspace(
    -5.0,
    5.0,
    201,
)

p_values = np.linspace(
    -5.0,
    5.0,
    201,
)


states = {
    "Coherent state": coherent_state(
        alpha=1.5,
        cutoff=cutoff,
    ),
    "Even cat state": even_cat_state(
        alpha=1.5,
        cutoff=cutoff,
    ),
    "Squeezed vacuum": squeezed_vacuum_state(
        squeezing_magnitude=0.7,
        squeezing_phase=0.0,
        cutoff=cutoff,
    ),
    "Thermal state": thermal_state(
        mean_photon_number=1.5,
        cutoff=cutoff,
    ),
}


for state_name, state in states.items():
    _, _, wigner = plot_wigner(
        state,
        x_values=x_values,
        p_values=p_values,
        title=state_name,
        show=False,
    )

    normalization = wigner_normalization(
        wigner=wigner,
        x_values=x_values,
        p_values=p_values,
    )

    negativity = wigner_negativity(
        wigner=wigner,
        x_values=x_values,
        p_values=p_values,
    )

    print(state_name)
    print("-" * len(state_name))
    print(
        f"Wigner normalization: "
        f"{normalization:.8f}"
    )
    print(
        f"Wigner negativity: "
        f"{negativity:.8f}"
    )
    print()


plt.show()