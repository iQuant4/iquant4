import numpy as np

from iqcore.optics import (
    apply_beam_splitter,
    beam_splitter_angle,
    beam_splitter_unitary,
    mean_mode_photon_numbers,
    total_photon_number_error,
    unitary_error,
)
from iqcore.states import (
    basis_index,
    reduced_state,
    tensor_product,
)
from iqcore.states import (
    purity,
)
from iqcore.states import (
    coherent_state,
    fock_state,
)
from iqcore.metrics import mean_photon_number


cutoff = 12

dimensions = (
    cutoff,
    cutoff,
)


print("Beam-splitter unitary")
print("---------------------")

unitary = beam_splitter_unitary(
    dimensions,
    transmissivity=0.5,
)

print(
    "Matrix shape:",
    unitary.shape,
)

print(
    "Unitarity error:",
    unitary_error(unitary),
)

print(
    "50:50 angle:",
    beam_splitter_angle(0.5),
)


print()
print("Coherent-state splitting")
print("------------------------")

alpha = 1.5

coherent = coherent_state(
    alpha=alpha,
    cutoff=cutoff,
)

vacuum = fock_state(
    photon_number=0,
    cutoff=cutoff,
)

coherent_vacuum = tensor_product(
    coherent,
    vacuum,
)

split_coherent = apply_beam_splitter(
    coherent_vacuum,
    dimensions=dimensions,
    transmissivity=0.5,
)

input_mean_a, input_mean_b = (
    mean_mode_photon_numbers(
        coherent_vacuum,
        dimensions,
    )
)

output_mean_a, output_mean_b = (
    mean_mode_photon_numbers(
        split_coherent,
        dimensions,
    )
)

print(
    "Input mean photons:",
    input_mean_a,
    input_mean_b,
)

print(
    "Output mean photons:",
    output_mean_a,
    output_mean_b,
)

print(
    "Expected output in each mode:",
    0.5 * abs(alpha) ** 2,
)

print(
    "Total photon-number error:",
    total_photon_number_error(
        coherent_vacuum,
        split_coherent,
        dimensions,
    ),
)

reduced_a = reduced_state(
    split_coherent,
    dimensions=dimensions,
    keep=0,
)

reduced_b = reduced_state(
    split_coherent,
    dimensions=dimensions,
    keep=1,
)

print(
    "Reduced-state purity, mode A:",
    purity(reduced_a),
)

print(
    "Reduced-state purity, mode B:",
    purity(reduced_b),
)

print(
    "Reduced mean photons, mode A:",
    mean_photon_number(reduced_a),
)

print(
    "Reduced mean photons, mode B:",
    mean_photon_number(reduced_b),
)


print()
print("Hong-Ou-Mandel interference")
print("---------------------------")

single_photon_a = fock_state(
    photon_number=1,
    cutoff=cutoff,
)

single_photon_b = fock_state(
    photon_number=1,
    cutoff=cutoff,
)

two_single_photons = tensor_product(
    single_photon_a,
    single_photon_b,
)

hom_output = apply_beam_splitter(
    two_single_photons,
    dimensions=dimensions,
    transmissivity=0.5,
)

index_20 = basis_index(
    occupations=(2, 0),
    dimensions=dimensions,
)

index_11 = basis_index(
    occupations=(1, 1),
    dimensions=dimensions,
)

index_02 = basis_index(
    occupations=(0, 2),
    dimensions=dimensions,
)

probability_20 = float(
    abs(hom_output[index_20]) ** 2
)

probability_11 = float(
    abs(hom_output[index_11]) ** 2
)

probability_02 = float(
    abs(hom_output[index_02]) ** 2
)

print(
    "P(2,0):",
    probability_20,
)

print(
    "P(1,1):",
    probability_11,
)

print(
    "P(0,2):",
    probability_02,
)

print(
    "Relevant amplitudes:"
)

print(
    "Amplitude |2,0>:",
    hom_output[index_20],
)

print(
    "Amplitude |1,1>:",
    hom_output[index_11],
)

print(
    "Amplitude |0,2>:",
    hom_output[index_02],
)

print(
    "Total photon-number error:",
    total_photon_number_error(
        two_single_photons,
        hom_output,
        dimensions,
    ),
)