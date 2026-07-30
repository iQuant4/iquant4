from __future__ import annotations

import numpy as np
import pytest

from iq4comm.channels import (
    FiberChannel,
    attenuation_db_to_transmissivity,
    fiber_transmissivity,
)
from iqcore.channels import (
    pure_loss_channel,
    pure_loss_kraus_operators,
)
from iqcore.measurements import quadrature_probability_density
from iqcore.measurements.homodyne_sampling import (
    quadrature_probability_density as pure_state_quadrature_density,
    sample_from_density,
    sign_free_samples,
)
from iqcore.optics import (
    SignFreeOPA,
    phase_shift_channel,
    phase_shift_operator,
)
from iqcore.states import (
    coherent_state,
    density_matrix,
    even_cat_state,
    fock_state,
)


def mean_photon_number(state: np.ndarray) -> float:
    rho = density_matrix(state)
    return float(
        np.sum(
            np.arange(rho.shape[0], dtype=float)
            * np.real(np.diag(rho))
        )
    )


def test_pure_loss_kraus_completeness() -> None:
    cutoff = 8
    operators = pure_loss_kraus_operators(
        transmissivity=0.37,
        cutoff=cutoff,
    )

    completeness = sum(
        operator.conjugate().T @ operator
        for operator in operators
    )

    assert completeness == pytest.approx(
        np.eye(cutoff),
        abs=1e-12,
    )


def test_pure_loss_identity_channel() -> None:
    state = even_cat_state(alpha=1.2, cutoff=20)

    output = pure_loss_channel(
        state,
        transmissivity=1.0,
    )

    assert output == pytest.approx(
        density_matrix(state),
        abs=1e-12,
    )


def test_complete_loss_maps_fock_state_to_vacuum() -> None:
    output = pure_loss_channel(
        fock_state(photon_number=3, cutoff=8),
        transmissivity=0.0,
    )

    vacuum = fock_state(photon_number=0, cutoff=8)

    assert output == pytest.approx(
        density_matrix(vacuum),
        abs=1e-12,
    )


def test_pure_loss_scales_mean_photon_number() -> None:
    state = coherent_state(alpha=1.4 + 0.3j, cutoff=30)
    transmissivity = 0.42

    output = pure_loss_channel(
        state,
        transmissivity=transmissivity,
    )

    assert mean_photon_number(output) == pytest.approx(
        transmissivity * mean_photon_number(state),
        rel=1e-10,
        abs=1e-12,
    )


def test_phase_shift_operator_is_unitary() -> None:
    operator = phase_shift_operator(
        phase=0.73,
        cutoff=12,
    )

    assert operator.conjugate().T @ operator == pytest.approx(
        np.eye(12),
        abs=1e-12,
    )


def test_phase_shift_rotates_coherent_amplitude() -> None:
    alpha = 0.8 + 0.2j
    phase = np.pi / 3.0
    cutoff = 25

    output = phase_shift_channel(
        coherent_state(alpha=alpha, cutoff=cutoff),
        phase=phase,
    )
    expected = coherent_state(
        alpha=alpha * np.exp(1j * phase),
        cutoff=cutoff,
    )

    assert output == pytest.approx(
        density_matrix(expected),
        abs=1e-10,
    )


def test_attenuation_conversions() -> None:
    assert attenuation_db_to_transmissivity(10.0) == pytest.approx(0.1)
    assert fiber_transmissivity(50.0, 0.2) == pytest.approx(0.1)

    with pytest.raises(ValueError, match="Attenuation"):
        attenuation_db_to_transmissivity(-1.0)

    with pytest.raises(ValueError, match="Distance"):
        fiber_transmissivity(-1.0)


def test_fiber_channel_uses_shared_attenuation_rule() -> None:
    channel = FiberChannel(attenuation_db_per_km=0.18)

    assert channel.transmittance(42.0) == pytest.approx(
        fiber_transmissivity(42.0, 0.18)
    )


def test_sign_free_opa_round_trip() -> None:
    opa = SignFreeOPA(
        gain_parameter=0.8,
        phase=0.2,
    )
    samples = np.array([-1.5, -0.25, 0.0, 0.75])

    power = opa.measure_power(samples)
    recovered = opa.recover_sign_free_quadrature(power)

    assert opa.power_gain == pytest.approx(np.exp(1.6))
    assert opa.gain_db == pytest.approx(10.0 * np.log10(np.exp(1.6)))
    assert recovered == pytest.approx(np.abs(samples))

    with pytest.raises(ValueError, match="Power samples"):
        opa.recover_sign_free_quadrature(np.array([-1.0]))


def test_pure_state_quadrature_density_matches_general_engine() -> None:
    state = coherent_state(alpha=0.7 - 0.3j, cutoff=25)
    grid = np.linspace(-5.0, 5.0, 2001)
    phase = 0.42

    specialized = pure_state_quadrature_density(
        state=state,
        x_values=grid,
        phase=phase,
    )
    general = quadrature_probability_density(
        state=state,
        x_values=grid,
        angle=phase,
    )

    assert specialized == pytest.approx(
        general,
        abs=1e-11,
    )


def test_density_sampling_and_sign_free_conversion() -> None:
    grid = np.linspace(-4.0, 4.0, 801)
    density = np.exp(-grid**2)
    rng_a = np.random.default_rng(7)
    rng_b = np.random.default_rng(7)

    samples_a = sample_from_density(
        grid,
        density,
        sample_count=1_000,
        rng=rng_a,
    )
    samples_b = sample_from_density(
        grid,
        density,
        sample_count=1_000,
        rng=rng_b,
    )

    assert samples_a == pytest.approx(samples_b)
    assert sign_free_samples(samples_a) == pytest.approx(
        np.abs(samples_a)
    )


def test_legacy_optics_imports_match_canonical_objects() -> None:
    from opa import SignFreeOPA as LegacySignFreeOPA
    from optical_channels import (
        fiber_transmissivity as legacy_fiber_transmissivity,
        phase_shift_channel as legacy_phase_shift_channel,
        pure_loss_channel as legacy_pure_loss_channel,
    )
    from quadrature import (
        sample_from_density as legacy_sample_from_density,
        sign_free_samples as legacy_sign_free_samples,
    )

    assert LegacySignFreeOPA is SignFreeOPA
    assert legacy_fiber_transmissivity is fiber_transmissivity
    assert legacy_phase_shift_channel is phase_shift_channel
    assert legacy_pure_loss_channel is pure_loss_channel
    assert legacy_sample_from_density is sample_from_density
    assert legacy_sign_free_samples is sign_free_samples
