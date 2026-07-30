import numpy as np

from iqcore.states import (
    displaced_squeezed_state,
    squeezed_vacuum_state,
    thermal_state,
    two_mode_squeezed_vacuum_state,
)


cutoff = 30

squeezed_state = squeezed_vacuum_state(
    squeezing_magnitude=0.7,
    squeezing_phase=0.0,
    cutoff=cutoff,
)

displaced_state = displaced_squeezed_state(
    alpha=1.0 + 0.2j,
    squeezing_magnitude=0.7,
    squeezing_phase=0.0,
    cutoff=cutoff,
)

thermal_density_matrix = thermal_state(
    mean_photon_number=1.5,
    cutoff=cutoff,
)

tmsv_state = two_mode_squeezed_vacuum_state(
    squeezing_magnitude=0.7,
    squeezing_phase=0.0,
    cutoff=15,
)


print("Squeezed vacuum")
print("----------------")
print(
    "Norm:",
    np.linalg.norm(squeezed_state),
)
print(
    "Odd population:",
    np.sum(
        np.abs(
            squeezed_state[1::2]
        ) ** 2
    ),
)


print("\nDisplaced squeezed state")
print("-------------------------")
print(
    "Norm:",
    np.linalg.norm(displaced_state),
)


print("\nThermal state")
print("-------------")
print(
    "Trace:",
    np.trace(
        thermal_density_matrix
    ),
)
print(
    "Hermiticity error:",
    np.linalg.norm(
        thermal_density_matrix
        - thermal_density_matrix.conjugate().T
    ),
)
print(
    "Purity:",
    np.real(
        np.trace(
            thermal_density_matrix
            @ thermal_density_matrix
        )
    ),
)


print("\nTwo-mode squeezed vacuum")
print("------------------------")
print(
    "Norm:",
    np.linalg.norm(tmsv_state),
)

tmsv_matrix = tmsv_state.reshape(
    15,
    15,
)

off_diagonal_population = (
    np.sum(
        np.abs(tmsv_matrix) ** 2
    )
    - np.sum(
        np.abs(
            np.diag(tmsv_matrix)
        ) ** 2
    )
)

print(
    "Population outside |n,n>:",
    off_diagonal_population,
)