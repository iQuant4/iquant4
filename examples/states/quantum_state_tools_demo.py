from iqcore.states import (
    density_matrix,
    validate_quantum_state,
)
from iqcore.states import (
    coherent_state,
    thermal_state,
)


coherent = coherent_state(
    alpha=1.5,
    cutoff=30,
)

thermal = thermal_state(
    mean_photon_number=1.5,
    cutoff=30,
)


print("Coherent state")
print("----------------")
print(
    validate_quantum_state(
        coherent
    )
)

print()

print("Thermal state")
print("-------------")
print(
    validate_quantum_state(
        thermal
    )
)

print()

coherent_density_matrix = density_matrix(
    coherent
)

print(
    "Converted coherent-state shape:",
    coherent_density_matrix.shape,
)