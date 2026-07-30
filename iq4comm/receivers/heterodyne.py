import numpy as np
from scipy.stats import norm

from iq4comm.metrics.receiver import ReceiverMetrics
from iq4comm.models.channel_state import ChannelState
from iq4comm.receivers.base import AnalyticalReceiver


class HeterodyneReceiver(AnalyticalReceiver):
    """
    Single-threshold heterodyne receiver.

    The complex heterodyne outcome is

        z = x + i y

    For a coherent state |alpha>, this implementation uses

        x ~ N(sqrt(eta) Re(alpha), 1/2 + xi)
        y ~ N(sqrt(eta) Im(alpha), 1/2 + xi)

    where xi is the excess-noise variance per quadrature.

    For the present binary real-amplitude source, the decision
    depends only on the real quadrature:

        Re(z) <= threshold -> 0
        Re(z) > threshold  -> 1
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
        return 0.5 + self.excess_noise_variance

    def measurement_mean(
        self,
        state: ChannelState,
    ) -> complex:
        return (
            np.sqrt(self.efficiency)
            * state.alpha
        )

    def measure(
        self,
        state: ChannelState,
    ) -> complex:
        mean = self.measurement_mean(state)

        standard_deviation = np.sqrt(
            self.quadrature_variance
        )

        real_part = self.rng.normal(
            loc=np.real(mean),
            scale=standard_deviation,
        )

        imaginary_part = self.rng.normal(
            loc=np.imag(mean),
            scale=standard_deviation,
        )

        return complex(
            real_part,
            imaginary_part,
        )

    def decide(
        self,
        measurement: complex,
    ) -> int:
        return (
            0
            if np.real(measurement) <= self.threshold
            else 1
        )

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

        mean_0 = np.real(
            self.measurement_mean(state_0)
        )

        mean_1 = np.real(
            self.measurement_mean(state_1)
        )

        standard_deviation = np.sqrt(
            self.quadrature_variance
        )

        error_given_0 = 1.0 - norm.cdf(
            self.threshold,
            loc=mean_0,
            scale=standard_deviation,
        )

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

class ErasureHeterodyneReceiver(AnalyticalReceiver):
    """
    Two-threshold heterodyne receiver.

    The real part of the complex outcome is used for the
    present real-amplitude binary source.

    Decision rule:

        Re(z) <= lower_threshold -> 0

        lower_threshold < Re(z) < upper_threshold
            -> erasure

        Re(z) >= upper_threshold -> 1
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

    def measurement_mean(
        self,
        state: ChannelState,
    ) -> complex:
        return (
            np.sqrt(self.efficiency)
            * state.alpha
        )

    def measure(
        self,
        state: ChannelState,
    ) -> complex:
        mean = self.measurement_mean(state)

        standard_deviation = np.sqrt(
            self.quadrature_variance
        )

        real_part = self.rng.normal(
            loc=np.real(mean),
            scale=standard_deviation,
        )

        imaginary_part = self.rng.normal(
            loc=np.imag(mean),
            scale=standard_deviation,
        )

        return complex(
            real_part,
            imaginary_part,
        )

    def decide(
        self,
        measurement: complex,
    ) -> int | None:
        real_part = np.real(measurement)

        if real_part <= self.lower_threshold:
            return 0

        if real_part >= self.upper_threshold:
            return 1

        return None

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

        mean_0 = np.real(
            self.measurement_mean(state_0)
        )

        mean_1 = np.real(
            self.measurement_mean(state_1)
        )

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