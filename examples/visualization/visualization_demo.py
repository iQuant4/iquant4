import matplotlib.pyplot as plt

from iqcore.states import (
    coherent_state,
    even_cat_state,
    squeezed_vacuum_state,
    thermal_state,
)
from iqcore.visualization import (
    plot_density_matrix,
    plot_fock_distribution,
    print_state_summary,
)


cutoff = 30

coherent = coherent_state(
    alpha=1.5,
    cutoff=cutoff,
)

cat = even_cat_state(
    alpha=1.5,
    cutoff=cutoff,
)

squeezed = squeezed_vacuum_state(
    squeezing_magnitude=0.7,
    squeezing_phase=0.0,
    cutoff=cutoff,
)

thermal = thermal_state(
    mean_photon_number=1.5,
    cutoff=cutoff,
)


print_state_summary(
    coherent,
    name="Coherent state",
)

print()

print_state_summary(
    cat,
    name="Even cat state",
)

print()

print_state_summary(
    squeezed,
    name="Squeezed vacuum",
)

print()

print_state_summary(
    thermal,
    name="Thermal state",
)


plot_fock_distribution(
    coherent,
    maximum_photon_number=15,
    title="Coherent-state photon-number distribution",
)

plot_fock_distribution(
    cat,
    maximum_photon_number=15,
    title="Even cat-state photon-number distribution",
)

plot_fock_distribution(
    squeezed,
    maximum_photon_number=15,
    title="Squeezed-vacuum photon-number distribution",
)

plot_fock_distribution(
    thermal,
    maximum_photon_number=15,
    title="Thermal-state photon-number distribution",
)


plot_density_matrix(
    coherent,
    component="magnitude",
    title="Coherent-state density matrix",
)

plot_density_matrix(
    cat,
    component="magnitude",
    title="Even cat-state density matrix",
)

plot_density_matrix(
    squeezed,
    component="magnitude",
    title="Squeezed-vacuum density matrix",
)

plot_density_matrix(
    thermal,
    component="magnitude",
    title="Thermal-state density matrix",
)

plt.show()