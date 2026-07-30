from collections.abc import Iterable
from dataclasses import dataclass

from iq4comm.metrics.receiver import ReceiverMetrics
from iq4comm.models.channel_state import ChannelState
from iq4comm.receivers.base import AnalyticalReceiver


@dataclass(frozen=True)
class OptimizationResult:
    """
    Result returned by the generic receiver optimizer.
    """

    receiver: AnalyticalReceiver
    metrics: ReceiverMetrics


def optimize_receiver(
    candidates: Iterable[AnalyticalReceiver],
    state_0: ChannelState,
    state_1: ChannelState,
    minimum_acceptance: float = 0.0,
    prior_0: float = 0.5,
    prior_1: float = 0.5,
) -> OptimizationResult:
    """
    Select the candidate receiver with the lowest conditional BER
    subject to a minimum acceptance-probability constraint.

    This function contains no receiver-specific formulas.
    """

    if not 0.0 <= minimum_acceptance <= 1.0:
        raise ValueError(
            "minimum_acceptance must be between 0 and 1."
        )

    best_result: OptimizationResult | None = None

    for receiver in candidates:
        metrics = receiver.analytical_metrics(
            state_0=state_0,
            state_1=state_1,
            prior_0=prior_0,
            prior_1=prior_1,
        )

        if (
            metrics.acceptance_probability
            < minimum_acceptance
        ):
            continue

        candidate_result = OptimizationResult(
            receiver=receiver,
            metrics=metrics,
        )

        if best_result is None:
            best_result = candidate_result
            continue

        best_metrics = best_result.metrics

        if (
            metrics.conditional_ber
            < best_metrics.conditional_ber
        ):
            best_result = candidate_result

        elif (
            metrics.conditional_ber
            == best_metrics.conditional_ber
            and metrics.acceptance_probability
            > best_metrics.acceptance_probability
        ):
            best_result = candidate_result

    if best_result is None:
        raise ValueError(
            "No receiver candidate satisfies the "
            "minimum acceptance constraint."
        )

    return best_result