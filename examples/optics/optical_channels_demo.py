import matplotlib.pyplot as plt
import numpy as np

from iq4comm.channels import fiber_transmissivity
from iqcore.channels import pure_loss_channel
from iqcore.optics import phase_shift_channel
from iqcore.phase_space import (
    plot_wigner,
    wigner_negativity,
    wigner_normalization,
)
from iqcore.states import (
    coherent_state,
    even_cat_state,
    purity,
    validate_quantum_state,
)
from iqcore.metrics import mean_photon_number


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


cat_state = even_cat_state(
    alpha=1.5,
    cutoff=cutoff,
)


transmissivities = [
    1.0,
    0.8,
    0.5,
    0.2,
]


for transmissivity in transmissivities:
    output_state = pure_loss_channel(
        cat_state,
        transmissivity=transmissivity,
    )

    _, _, wigner = plot_wigner(
        output_state,
        x_values=x_values,
        p_values=p_values,
        title=(
            "Even cat after pure loss: "
            rf"$\eta={transmissivity:.1f}$"
        ),
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

    print(
        f"Transmissivity eta = "
        f"{transmissivity:.1f}"
    )
    print("-" * 28)

    print(
        "Mean photon number: "
        f"{mean_photon_number(output_state):.8f}"
    )

    print(
        "Purity: "
        f"{purity(output_state):.8f}"
    )

    print(
        "Wigner normalization: "
        f"{normalization:.8f}"
    )

    print(
        "Wigner negativity: "
        f"{negativity:.8f}"
    )

    print()


coherent = coherent_state(
    alpha=1.5,
    cutoff=cutoff,
)

rotated_coherent = phase_shift_channel(
    coherent,
    phase=np.pi / 2.0,
)

plot_wigner(
    coherent,
    x_values=x_values,
    p_values=p_values,
    title="Original coherent state",
    show=False,
)

plot_wigner(
    rotated_coherent,
    x_values=x_values,
    p_values=p_values,
    title=r"Coherent state after phase shift $\phi=\pi/2$",
    show=False,
)


distance_km = 50.0

eta_fiber = fiber_transmissivity(
    distance_km=distance_km,
    loss_db_per_km=0.2,
)

print(
    f"Fiber transmissivity at "
    f"{distance_km:.1f} km: "
    f"{eta_fiber:.8f}"
)

fiber_output = pure_loss_channel(
    cat_state,
    transmissivity=eta_fiber,
)

print(
    validate_quantum_state(
        fiber_output
    )
)


plt.show()