"""Integration tests tying the fiber engine into the wider iQuant4 platform.

These verify that ``iqcore.fiber`` is exposed like the other core subpackages,
that the shared ``FiberSpec`` drives the quantum pure-loss channel, that the
communications ``FiberChannel`` can be built from the same spec, and -- most
importantly -- that both branches compute the *same* span loss.
"""

from __future__ import annotations

import numpy as np
import pytest

import iqcore as iq
import iq4comm as iqc
from iqcore.fiber import FiberSpec, SMF28


def test_fiber_is_exposed_as_core_subpackage():
    """``iqcore.fiber`` loads through the lazy loader like iqcore.states."""
    assert hasattr(iq, "fiber")
    assert hasattr(iq.fiber, "propagate")
    assert hasattr(iq.fiber, "SMF28")
    assert "fiber" in iq.__all__


def test_cross_branch_transmissivity_is_consistent():
    """iqcore FiberSpec and iq4comm agree on span transmissivity to the bit."""
    alpha_db = 0.2
    for length in (0.0, 10.0, 40.0, 123.4):
        spec = FiberSpec(attenuation_db_per_km=alpha_db, name="consistency")
        core_eta = spec.transmissivity(length)
        comm_eta = iqc.fiber_transmissivity(
            distance_km=length, loss_db_per_km=alpha_db
        )
        assert core_eta == pytest.approx(comm_eta, rel=0.0, abs=0.0)


def test_fiber_channel_from_spec_matches_spec():
    """FiberChannel.from_spec inherits the spec's attenuation and retains it."""
    channel = iqc.FiberChannel.from_spec(SMF28)
    assert channel.attenuation_db_per_km == SMF28.attenuation_db_per_km
    assert channel.spec is SMF28
    for length in (0.0, 25.0, 80.0):
        assert channel.transmittance(length) == pytest.approx(
            SMF28.transmissivity(length), rel=1e-12
        )


def test_fiber_loss_channel_drives_quantum_channel():
    """The shared spec drives the bosonic pure-loss channel via iqcore.channels."""
    from iqcore.channels import fiber_loss_channel, pure_loss_channel
    from iqcore.states import coherent_state

    cutoff = 30
    state = coherent_state(alpha=1.2, cutoff=cutoff)
    length = 50.0

    rho_via_spec = fiber_loss_channel(state, SMF28, length)
    rho_direct = pure_loss_channel(state, SMF28.transmissivity(length))

    # Same physics: identical output density matrices.
    assert np.allclose(rho_via_spec, rho_direct)
    # Valid density matrix: unit trace, Hermitian.
    assert np.trace(rho_via_spec) == pytest.approx(1.0)
    assert np.allclose(rho_via_spec, rho_via_spec.conj().T)


def test_fiber_channel_propagate_still_works():
    """The pre-existing FiberChannel API is unchanged (non-breaking)."""
    channel = iqc.FiberChannel(attenuation_db_per_km=0.2)
    out = channel.propagate(mu=4.0, alpha=2.0 + 0j, distance_km=20.0)
    eta = channel.transmittance(20.0)
    assert out.mu == pytest.approx(eta * 4.0)
    assert out.alpha == pytest.approx(np.sqrt(eta) * 2.0)
