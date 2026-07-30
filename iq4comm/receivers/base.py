from abc import ABC, abstractmethod
from typing import Any

from iq4comm.metrics.receiver import ReceiverMetrics
from iq4comm.models.channel_state import ChannelState


class Receiver(ABC):
    """
    Base class for physical receiver implementations.
    """

    @abstractmethod
    def measure(self, state: ChannelState) -> Any:
        """
        Perform a receiver measurement.
        """

    @abstractmethod
    def decide(self, measurement: Any) -> int | None:
        """
        Convert a measurement into a decision.

        Returns:
            0 or 1 for an accepted binary decision.
            None for an erased observation.
        """

    def detect(self, state: ChannelState) -> int | None:
        """
        Measure the state and make a decision.
        """

        measurement = self.measure(state)
        return self.decide(measurement)


class AnalyticalReceiver(Receiver):
    """
    Base class for receivers with an analytical performance model.
    """

    @abstractmethod
    def analytical_metrics(
        self,
        state_0: ChannelState,
        state_1: ChannelState,
        prior_0: float = 0.5,
        prior_1: float = 0.5,
    ) -> ReceiverMetrics:
        """
        Calculate receiver performance for two input states.
        """