from dataclasses import dataclass


@dataclass(frozen=True)
class ReceiverMetrics:
    """
    Standard performance results returned by any receiver model.
    """

    acceptance_probability: float
    erasure_probability: float
    unconditional_error_probability: float
    conditional_ber: float

    def __post_init__(self) -> None:
        probability_fields = {
            "acceptance_probability": self.acceptance_probability,
            "erasure_probability": self.erasure_probability,
            "unconditional_error_probability": (
                self.unconditional_error_probability
            ),
            "conditional_ber": self.conditional_ber,
        }

        for name, value in probability_fields.items():
            if not 0.0 <= value <= 1.0:
                raise ValueError(
                    f"{name} must be between 0 and 1."
                )