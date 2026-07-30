import numpy as np

from iqcore.states import (
    basis_index,
    basis_occupations,
    density_tensor_product,
    partial_trace,
    product_state_dimensions,
    reduced_state,
    tensor_product,
    total_dimension,
)
from iqcore.states import (
    purity,
    validate_quantum_state,
)
from iqcore.states import (
    coherent_state,
    fock_state,
    thermal_state,
)


cutoff = 10

vacuum = fock_state(
    photon_number=0,
    cutoff=cutoff,
)

single_photon = fock_state(
    photon_number=1,
    cutoff=cutoff,
)

coherent = coherent_state(
    alpha=1.0,
    cutoff=cutoff,
)

thermal = thermal_state(
    mean_photon_number=0.5,
    cutoff=cutoff,
)


print("Two-mode ket")
print("------------")

two_mode_ket = tensor_product(
    single_photon,
    vacuum,
)

dimensions = product_state_dimensions(
    single_photon,
    vacuum,
)

print(
    "Dimensions:",
    dimensions,
)

print(
    "Total dimension:",
    total_dimension(dimensions),
)

print(
    "Ket shape:",
    two_mode_ket.shape,
)

print(
    "Ket norm:",
    np.linalg.norm(two_mode_ket),
)

expected_index = basis_index(
    occupations=(1, 0),
    dimensions=dimensions,
)

print(
    "Index of |1,0>:",
    expected_index,
)

print(
    "Amplitude at |1,0>:",
    two_mode_ket[expected_index],
)

print(
    "Occupations recovered from index:",
    basis_occupations(
        expected_index,
        dimensions,
    ),
)


print()
print("Product-state partial trace")
print("---------------------------")

coherent_vacuum = tensor_product(
    coherent,
    vacuum,
)

coherent_reduced = reduced_state(
    coherent_vacuum,
    dimensions=(cutoff, cutoff),
    keep=0,
)

vacuum_reduced = reduced_state(
    coherent_vacuum,
    dimensions=(cutoff, cutoff),
    keep=1,
)

coherent_reference = np.outer(
    coherent,
    coherent.conjugate(),
)

vacuum_reference = np.outer(
    vacuum,
    vacuum.conjugate(),
)

print(
    "Coherent reduced-state error:",
    np.linalg.norm(
        coherent_reduced
        - coherent_reference
    ),
)

print(
    "Vacuum reduced-state error:",
    np.linalg.norm(
        vacuum_reduced
        - vacuum_reference
    ),
)


print()
print("Mixed product state")
print("-------------------")

mixed_product = density_tensor_product(
    coherent,
    thermal,
)

print(
    "Composite shape:",
    mixed_product.shape,
)

print(
    "Composite validation:",
    validate_quantum_state(
        mixed_product
    ),
)

thermal_reduced = partial_trace(
    mixed_product,
    dimensions=(cutoff, cutoff),
    trace_out=0,
)

print(
    "Recovered thermal-state error:",
    np.linalg.norm(
        thermal_reduced
        - thermal
    ),
)

print(
    "Composite purity:",
    purity(mixed_product),
)

print(
    "Expected product purity:",
    purity(coherent)
    * purity(thermal),
)