from __future__ import annotations

import numpy as np
import pytest

from iq4comm import (
    AnalyticalReceiver,
    BinaryCoherentSource,
    ChannelState,
    ErasureHeterodyneReceiver,
    ErasureHomodyneReceiver,
    ErasurePNRReceiver,
    FiberChannel,
    HeterodyneReceiver,
    HomodyneReceiver,
    PNRReceiver,
    Receiver,
    ReceiverMetrics,
    erasure_pnr_metrics,
    optimize_receiver,
)


def make_binary_states(
    mu_0: float = 2.0,
    mu_1: float = 8.0,
    distance_km: float = 0.0,
) -> tuple[ChannelState, ChannelState]:
    source = BinaryCoherentSource(mu_0=mu_0, mu_1=mu_1)
    channel = FiberChannel(attenuation_db_per_km=0.2)

    state_0 = channel.propagate(
        mu=source.mean_photon_number(0),
        alpha=source.amplitude(0),
        distance_km=distance_km,
    )
    state_1 = channel.propagate(
        mu=source.mean_photon_number(1),
        alpha=source.amplitude(1),
        distance_km=distance_km,
    )
    return state_0, state_1


def test_channel_state_validation() -> None:
    state = ChannelState(
        mu=2.0,
        alpha=np.sqrt(2.0),
        distance_km=10.0,
        transmittance=0.5,
    )
    assert state.mu == pytest.approx(2.0)

    with pytest.raises(ValueError, match="Mean photon number"):
        ChannelState(-1.0, 0.0, 0.0, 1.0)

    with pytest.raises(ValueError, match="Distance"):
        ChannelState(1.0, 1.0, -1.0, 1.0)

    with pytest.raises(ValueError, match="Transmittance"):
        ChannelState(1.0, 1.0, 0.0, 1.1)


def test_binary_coherent_source_mapping() -> None:
    source = BinaryCoherentSource(mu_0=2.0, mu_1=8.0)

    assert source.mean_photon_number(0) == pytest.approx(2.0)
    assert source.mean_photon_number(1) == pytest.approx(8.0)
    assert abs(source.amplitude(0)) ** 2 == pytest.approx(2.0)
    assert abs(source.amplitude(1)) ** 2 == pytest.approx(8.0)

    with pytest.raises(ValueError, match="Symbol"):
        source.mean_photon_number(2)

    with pytest.raises(ValueError, match="mu_1"):
        BinaryCoherentSource(mu_0=2.0, mu_1=2.0)


def test_fiber_channel_transmittance_and_propagation() -> None:
    channel = FiberChannel(attenuation_db_per_km=0.2)

    assert channel.transmittance(0.0) == pytest.approx(1.0)
    assert channel.transmittance(50.0) == pytest.approx(0.1)

    output = channel.propagate(
        mu=8.0,
        alpha=np.sqrt(8.0),
        distance_km=50.0,
    )

    assert output.transmittance == pytest.approx(0.1)
    assert output.mu == pytest.approx(0.8)
    assert output.alpha == pytest.approx(np.sqrt(0.8))


def test_receiver_metrics_validation() -> None:
    metrics = ReceiverMetrics(
        acceptance_probability=0.75,
        erasure_probability=0.25,
        unconditional_error_probability=0.02,
        conditional_ber=0.02 / 0.75,
    )
    assert metrics.acceptance_probability == pytest.approx(0.75)

    with pytest.raises(ValueError, match="conditional_ber"):
        ReceiverMetrics(1.0, 0.0, 0.0, 1.1)


def test_receiver_base_types_are_public() -> None:
    assert issubclass(AnalyticalReceiver, Receiver)
    assert issubclass(PNRReceiver, AnalyticalReceiver)
    assert issubclass(HomodyneReceiver, AnalyticalReceiver)
    assert issubclass(HeterodyneReceiver, AnalyticalReceiver)


def test_erasure_pnr_helper_matches_receiver() -> None:
    state_0, state_1 = make_binary_states()
    receiver = ErasurePNRReceiver(
        lower_threshold=3,
        upper_threshold=6,
    )

    receiver_metrics = receiver.analytical_metrics(state_0, state_1)
    helper_metrics = erasure_pnr_metrics(
        mu_0=2.0,
        mu_1=8.0,
        lower_threshold=3,
        upper_threshold=6,
    )

    assert receiver_metrics.acceptance_probability == pytest.approx(
        helper_metrics["acceptance_probability"]
    )
    assert receiver_metrics.erasure_probability == pytest.approx(
        helper_metrics["erasure_probability"]
    )
    assert receiver_metrics.unconditional_error_probability == pytest.approx(
        helper_metrics["unconditional_error_probability"]
    )
    assert receiver_metrics.conditional_ber == pytest.approx(
        helper_metrics["conditional_ber"]
    )


def test_known_pnr_erasure_regression() -> None:
    state_0, state_1 = make_binary_states()
    metrics = ErasurePNRReceiver(3, 6).analytical_metrics(state_0, state_1)

    assert metrics.acceptance_probability == pytest.approx(0.8624155594456101)
    assert metrics.erasure_probability == pytest.approx(0.1375844405543899)
    assert metrics.unconditional_error_probability == pytest.approx(
        0.029471860236149203
    )
    assert metrics.conditional_ber == pytest.approx(0.03417361840629906)


def test_threshold_decision_rules() -> None:
    pnr = ErasurePNRReceiver(3, 6)
    assert pnr.decide(3) == 0
    assert pnr.decide(4) is None
    assert pnr.decide(5) is None
    assert pnr.decide(6) == 1

    homodyne = ErasureHomodyneReceiver(2.0, 3.0)
    assert homodyne.decide(2.0) == 0
    assert homodyne.decide(2.5) is None
    assert homodyne.decide(3.0) == 1

    heterodyne = ErasureHeterodyneReceiver(1.0, 2.0)
    assert heterodyne.decide(1.0 + 5.0j) == 0
    assert heterodyne.decide(1.5 - 3.0j) is None
    assert heterodyne.decide(2.0 + 0.0j) == 1


def test_seeded_receiver_measurements_are_reproducible() -> None:
    state_0, _ = make_binary_states(distance_km=10.0)

    assert PNRReceiver(4, seed=7).measure(state_0) == PNRReceiver(
        4, seed=7
    ).measure(state_0)

    assert HomodyneReceiver(3.0, seed=7).measure(state_0) == pytest.approx(
        HomodyneReceiver(3.0, seed=7).measure(state_0)
    )

    assert HeterodyneReceiver(2.0, seed=7).measure(state_0) == pytest.approx(
        HeterodyneReceiver(2.0, seed=7).measure(state_0)
    )


def test_erasure_metrics_are_consistent() -> None:
    state_0, state_1 = make_binary_states()
    receivers = [
        ErasurePNRReceiver(3, 6),
        ErasureHomodyneReceiver(2.43, 3.53),
        ErasureHeterodyneReceiver(1.79, 2.49),
    ]

    for receiver in receivers:
        metrics = receiver.analytical_metrics(state_0, state_1)
        assert (
            metrics.acceptance_probability + metrics.erasure_probability
        ) == pytest.approx(1.0)
        assert metrics.conditional_ber == pytest.approx(
            metrics.unconditional_error_probability
            / metrics.acceptance_probability
        )


def test_optimizer_selects_best_feasible_receiver() -> None:
    state_0, state_1 = make_binary_states()
    candidates = [
        ErasurePNRReceiver(3, 5),
        ErasurePNRReceiver(3, 6),
        ErasurePNRReceiver(2, 6),
    ]

    result = optimize_receiver(
        candidates=candidates,
        state_0=state_0,
        state_1=state_1,
        minimum_acceptance=0.75,
    )

    assert isinstance(result.receiver, ErasurePNRReceiver)
    assert result.receiver.lower_threshold == 2
    assert result.receiver.upper_threshold == 6
    assert result.metrics.acceptance_probability >= 0.75
    assert result.metrics.conditional_ber == pytest.approx(
        0.020001594989548087
    )


def test_optimizer_rejects_infeasible_constraint() -> None:
    state_0, state_1 = make_binary_states()

    with pytest.raises(ValueError, match="No receiver candidate"):
        optimize_receiver(
            candidates=[ErasurePNRReceiver(2, 7)],
            state_0=state_0,
            state_1=state_1,
            minimum_acceptance=0.99,
        )


def test_legacy_communication_imports_match_canonical_objects() -> None:
    from channel import FiberChannel as LegacyFiberChannel
    from heterodyne import HeterodyneReceiver as LegacyHeterodyneReceiver
    from homodyne import HomodyneReceiver as LegacyHomodyneReceiver
    from metrics import erasure_pnr_metrics as legacy_erasure_pnr_metrics
    from optimizer import optimize_receiver as legacy_optimize_receiver
    from performance import ReceiverMetrics as LegacyReceiverMetrics
    from pnr import PNRReceiver as LegacyPNRReceiver
    from receiver import Receiver as LegacyReceiver
    from source import BinaryCoherentSource as LegacyBinaryCoherentSource
    from state import ChannelState as LegacyChannelState

    assert LegacyChannelState is ChannelState
    assert LegacyBinaryCoherentSource is BinaryCoherentSource
    assert LegacyFiberChannel is FiberChannel
    assert LegacyReceiver is Receiver
    assert LegacyReceiverMetrics is ReceiverMetrics
    assert LegacyPNRReceiver is PNRReceiver
    assert LegacyHomodyneReceiver is HomodyneReceiver
    assert LegacyHeterodyneReceiver is HeterodyneReceiver
    assert legacy_optimize_receiver is optimize_receiver
    assert legacy_erasure_pnr_metrics is erasure_pnr_metrics
