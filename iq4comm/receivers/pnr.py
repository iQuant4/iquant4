import numpy as np
from scipy.stats import poisson

from iq4comm.metrics.receiver import ReceiverMetrics
from iq4comm.models.channel_state import ChannelState
from iq4comm.receivers.base import AnalyticalReceiver


def _validate_detector_parameters(
    efficiency: float,
    dark_counts: float,
) -> None:
    if not 0.0 <= efficiency <= 1.0:
        raise ValueError(
            "Efficiency must be between 0 and 1."
        )

    if dark_counts < 0.0:
        raise ValueError(
            "Dark counts cannot be negative."
        )


def _validate_priors(
    prior_0: float,
    prior_1: float,
) -> None:
    if prior_0 < 0.0 or prior_1 < 0.0:
        raise ValueError(
            "Prior probabilities cannot be negative."
        )

    if not np.isclose(prior_0 + prior_1, 1.0):
        raise ValueError(
            "Prior probabilities must sum to 1."
        )


class PNRReceiver(AnalyticalReceiver):
    """
    Single-threshold photon-number-resolving receiver.

    Decision rule:
        count <= threshold -> 0
        count > threshold  -> 1
    """

    def __init__(
        self,
        threshold: int,
        efficiency: float = 1.0,
        dark_counts: float = 0.0,
        seed: int | None = None,
    ) -> None:
        if threshold < 0:
            raise ValueError(
                "Threshold cannot be negative."
            )

        _validate_detector_parameters(
            efficiency=efficiency,
            dark_counts=dark_counts,
        )

        self.threshold = threshold
        self.efficiency = efficiency
        self.dark_counts = dark_counts
        self.rng = np.random.default_rng(seed)

    def measure(self, state: ChannelState) -> int:
        detected_mean = (
            self.efficiency * state.mu
            + self.dark_counts
        )

        return int(
            self.rng.poisson(detected_mean)
        )

    def decide(self, count: int) -> int:
        return 0 if count <= self.threshold else 1

    def measure_and_decide(
        self,
        state: ChannelState,
    ) -> tuple[int, int]:
        count = self.measure(state)
        decision = self.decide(count)

        return count, decision

    def analytical_metrics(
        self,
        state_0: ChannelState,
        state_1: ChannelState,
        prior_0: float = 0.5,
        prior_1: float = 0.5,
    ) -> ReceiverMetrics:
        _validate_priors(
            prior_0=prior_0,
            prior_1=prior_1,
        )

        detected_mu_0 = (
            self.efficiency * state_0.mu
            + self.dark_counts
        )

        detected_mu_1 = (
            self.efficiency * state_1.mu
            + self.dark_counts
        )

        error_given_0 = 1.0 - poisson.cdf(
            self.threshold,
            detected_mu_0,
        )

        error_given_1 = poisson.cdf(
            self.threshold,
            detected_mu_1,
        )

        error_probability = (
            prior_0 * error_given_0
            + prior_1 * error_given_1
        )

        return ReceiverMetrics(
            acceptance_probability=1.0,
            erasure_probability=0.0,
            unconditional_error_probability=(
                error_probability
            ),
            conditional_ber=error_probability,
        )

    def __str__(self) -> str:
        return (
            "PNRReceiver("
            f"threshold={self.threshold}, "
            f"eta={self.efficiency:.3f}, "
            f"dark_counts={self.dark_counts:.3f}"
            ")"
        )


class ErasurePNRReceiver(AnalyticalReceiver):
    """
    Two-threshold PNR receiver with an erasure region.

    Decision rule:
        count <= lower_threshold -> 0
        lower_threshold < count < upper_threshold -> erasure
        count >= upper_threshold -> 1
    """

    def __init__(
        self,
        lower_threshold: int,
        upper_threshold: int,
        efficiency: float = 1.0,
        dark_counts: float = 0.0,
        seed: int | None = None,
    ) -> None:
        if lower_threshold < 0:
            raise ValueError(
                "Lower threshold cannot be negative."
            )

        if upper_threshold <= lower_threshold:
            raise ValueError(
                "Upper threshold must be greater than "
                "the lower threshold."
            )

        _validate_detector_parameters(
            efficiency=efficiency,
            dark_counts=dark_counts,
        )

        self.lower_threshold = lower_threshold
        self.upper_threshold = upper_threshold
        self.efficiency = efficiency
        self.dark_counts = dark_counts
        self.rng = np.random.default_rng(seed)

    def measure(self, state: ChannelState) -> int:
        detected_mean = (
            self.efficiency * state.mu
            + self.dark_counts
        )

        return int(
            self.rng.poisson(detected_mean)
        )

    def decide(self, count: int) -> int | None:
        if count <= self.lower_threshold:
            return 0

        if count >= self.upper_threshold:
            return 1

        return None

    def measure_and_decide(
        self,
        state: ChannelState,
    ) -> tuple[int, int | None]:
        count = self.measure(state)
        decision = self.decide(count)

        return count, decision

    def analytical_metrics(
        self,
        state_0: ChannelState,
        state_1: ChannelState,
        prior_0: float = 0.5,
        prior_1: float = 0.5,
    ) -> ReceiverMetrics:
        _validate_priors(
            prior_0=prior_0,
            prior_1=prior_1,
        )

        detected_mu_0 = (
            self.efficiency * state_0.mu
            + self.dark_counts
        )

        detected_mu_1 = (
            self.efficiency * state_1.mu
            + self.dark_counts
        )

        correct_given_0 = poisson.cdf(
            self.lower_threshold,
            detected_mu_0,
        )

        error_given_0 = 1.0 - poisson.cdf(
            self.upper_threshold - 1,
            detected_mu_0,
        )

        error_given_1 = poisson.cdf(
            self.lower_threshold,
            detected_mu_1,
        )

        correct_given_1 = 1.0 - poisson.cdf(
            self.upper_threshold - 1,
            detected_mu_1,
        )

        acceptance_probability = (
            prior_0
            * (correct_given_0 + error_given_0)
            + prior_1
            * (correct_given_1 + error_given_1)
        )

        erasure_probability = (
            1.0 - acceptance_probability
        )

        unconditional_error_probability = (
            prior_0 * error_given_0
            + prior_1 * error_given_1
        )

        conditional_ber = (
            unconditional_error_probability
            / acceptance_probability
            if acceptance_probability > 0.0
            else 0.0
        )

        return ReceiverMetrics(
            acceptance_probability=(
                acceptance_probability
            ),
            erasure_probability=(
                erasure_probability
            ),
            unconditional_error_probability=(
                unconditional_error_probability
            ),
            conditional_ber=conditional_ber,
        )

    def configuration(self) -> dict[str, int]:
        """
        Return the receiver's optimizable configuration.
        """

        return {
            "lower_threshold": self.lower_threshold,
            "upper_threshold": self.upper_threshold,
        }

    def __str__(self) -> str:
        return (
            "ErasurePNRReceiver("
            f"lower_threshold={self.lower_threshold}, "
            f"upper_threshold={self.upper_threshold}, "
            f"eta={self.efficiency:.3f}, "
            f"dark_counts={self.dark_counts:.3f}"
            ")"
        )