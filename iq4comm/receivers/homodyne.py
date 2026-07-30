import numpy as np
from scipy.stats import norm

from iq4comm.metrics.receiver import ReceiverMetrics
from iq4comm.models.channel_state import ChannelState
from iq4comm.receivers.base import AnalyticalReceiver


class HomodyneReceiver(AnalyticalReceiver):
    """
    Single-threshold homodyne receiver.

    Quadrature convention:

        x = (a + a†) / sqrt(2)

    For a coherent state |alpha>:

        mean(x) = sqrt(2) * Re(alpha)
        variance(x) = 1 / 2

    Decision rule:

        x <= threshold -> 0
        x > threshold  -> 1
    """

    def __init__(
        self,
        threshold: float,
        efficiency: float = 1.0,
        excess_noise_variance: float = 0.0,
        seed: int | None = None,
    ) -> None:
        if not 0.0 <= efficiency <= 1.0:
            raise ValueError(
                "Efficiency must be between 0 and 1."
            )

        if excess_noise_variance < 0.0:
            raise ValueError(
                "Excess-noise variance cannot be negative."
            )

        self.threshold = threshold
        self.efficiency = efficiency
        self.excess_noise_variance = (
            excess_noise_variance
        )
        self.rng = np.random.default_rng(seed)

    @property
    def quadrature_variance(self) -> float:
        """
        Total measured quadrature variance.

        The ideal coherent-state vacuum variance is 1/2.
        """

        return 0.5 + self.excess_noise_variance

    def quadrature_mean(
        self,
        state: ChannelState,
    ) -> float:
        """
        Mean measured x quadrature after detector loss.
        """

        detected_alpha = (
            np.sqrt(self.efficiency) * state.alpha
        )

        return float(
            np.sqrt(2.0) * np.real(detected_alpha)
        )

    def measure(
        self,
        state: ChannelState,
    ) -> float:
        mean = self.quadrature_mean(state)
        standard_deviation = np.sqrt(
            self.quadrature_variance
        )

        return float(
            self.rng.normal(
                loc=mean,
                scale=standard_deviation,
            )
        )

    def decide(
        self,
        measurement: float,
    ) -> int:
        return (
            0
            if measurement <= self.threshold
            else 1
        )

    def measure_and_decide(
        self,
        state: ChannelState,
    ) -> tuple[float, int]:
        measurement = self.measure(state)
        decision = self.decide(measurement)

        return measurement, decision

    def analytical_metrics(
        self,
        state_0: ChannelState,
        state_1: ChannelState,
        prior_0: float = 0.5,
        prior_1: float = 0.5,
    ) -> ReceiverMetrics:
        if prior_0 < 0.0 or prior_1 < 0.0:
            raise ValueError(
                "Prior probabilities cannot be negative."
            )

        if not np.isclose(
            prior_0 + prior_1,
            1.0,
        ):
            raise ValueError(
                "Prior probabilities must sum to 1."
            )

        mean_0 = self.quadrature_mean(state_0)
        mean_1 = self.quadrature_mean(state_1)

        standard_deviation = np.sqrt(
            self.quadrature_variance
        )

        # Error for symbol 0:
        # measurement exceeds the threshold.
        error_given_0 = 1.0 - norm.cdf(
            self.threshold,
            loc=mean_0,
            scale=standard_deviation,
        )

        # Error for symbol 1:
        # measurement is at or below the threshold.
        error_given_1 = norm.cdf(
            self.threshold,
            loc=mean_1,
            scale=standard_deviation,
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

    def configuration(
        self,
    ) -> dict[str, float]:
        return {
            "threshold": self.threshold,
            "efficiency": self.efficiency,
            "excess_noise_variance": (
                self.excess_noise_variance
            ),
        }

    def __str__(self) -> str:
        return (
            "HomodyneReceiver("
            f"threshold={self.threshold:.4f}, "
            f"eta={self.efficiency:.3f}, "
            f"excess_noise_variance="
            f"{self.excess_noise_variance:.4f}"
            ")"
        )

class ErasureHomodyneReceiver(AnalyticalReceiver):
    """
    Two-threshold homodyne receiver with an erasure region.

    Decision rule:

        x <= lower_threshold -> 0

        lower_threshold < x < upper_threshold
            -> erasure

        x >= upper_threshold -> 1
    """

    def __init__(
        self,
        lower_threshold: float,
        upper_threshold: float,
        efficiency: float = 1.0,
        excess_noise_variance: float = 0.0,
        seed: int | None = None,
    ) -> None:
        if upper_threshold <= lower_threshold:
            raise ValueError(
                "Upper threshold must be greater than "
                "the lower threshold."
            )

        if not 0.0 <= efficiency <= 1.0:
            raise ValueError(
                "Efficiency must be between 0 and 1."
            )

        if excess_noise_variance < 0.0:
            raise ValueError(
                "Excess-noise variance cannot be negative."
            )

        self.lower_threshold = lower_threshold
        self.upper_threshold = upper_threshold
        self.efficiency = efficiency
        self.excess_noise_variance = (
            excess_noise_variance
        )
        self.rng = np.random.default_rng(seed)

    @property
    def quadrature_variance(self) -> float:
        return 0.5 + self.excess_noise_variance

    def quadrature_mean(
        self,
        state: ChannelState,
    ) -> float:
        detected_alpha = (
            np.sqrt(self.efficiency) * state.alpha
        )

        return float(
            np.sqrt(2.0)
            * np.real(detected_alpha)
        )

    def measure(
        self,
        state: ChannelState,
    ) -> float:
        mean = self.quadrature_mean(state)

        standard_deviation = np.sqrt(
            self.quadrature_variance
        )

        return float(
            self.rng.normal(
                loc=mean,
                scale=standard_deviation,
            )
        )

    def decide(
        self,
        measurement: float,
    ) -> int | None:
        if measurement <= self.lower_threshold:
            return 0

        if measurement >= self.upper_threshold:
            return 1

        return None

    def measure_and_decide(
        self,
        state: ChannelState,
    ) -> tuple[float, int | None]:
        measurement = self.measure(state)
        decision = self.decide(measurement)

        return measurement, decision

    def analytical_metrics(
        self,
        state_0: ChannelState,
        state_1: ChannelState,
        prior_0: float = 0.5,
        prior_1: float = 0.5,
    ) -> ReceiverMetrics:
        if prior_0 < 0.0 or prior_1 < 0.0:
            raise ValueError(
                "Prior probabilities cannot be negative."
            )

        if not np.isclose(
            prior_0 + prior_1,
            1.0,
        ):
            raise ValueError(
                "Prior probabilities must sum to 1."
            )

        mean_0 = self.quadrature_mean(state_0)
        mean_1 = self.quadrature_mean(state_1)

        standard_deviation = np.sqrt(
            self.quadrature_variance
        )

        correct_given_0 = norm.cdf(
            self.lower_threshold,
            loc=mean_0,
            scale=standard_deviation,
        )

        error_given_0 = 1.0 - norm.cdf(
            self.upper_threshold,
            loc=mean_0,
            scale=standard_deviation,
        )

        error_given_1 = norm.cdf(
            self.lower_threshold,
            loc=mean_1,
            scale=standard_deviation,
        )

        correct_given_1 = 1.0 - norm.cdf(
            self.upper_threshold,
            loc=mean_1,
            scale=standard_deviation,
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

    def configuration(
        self,
    ) -> dict[str, float]:
        return {
            "lower_threshold": self.lower_threshold,
            "upper_threshold": self.upper_threshold,
            "efficiency": self.efficiency,
            "excess_noise_variance": (
                self.excess_noise_variance
            ),
        }

    def __str__(self) -> str:
        return (
            "ErasureHomodyneReceiver("
            f"lower_threshold="
            f"{self.lower_threshold:.4f}, "
            f"upper_threshold="
            f"{self.upper_threshold:.4f}, "
            f"eta={self.efficiency:.3f}, "
            f"excess_noise_variance="
            f"{self.excess_noise_variance:.4f}"
            ")"
        )
    