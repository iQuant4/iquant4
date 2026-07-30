from scipy.stats import poisson


def erasure_pnr_metrics(
    mu_0: float,
    mu_1: float,
    lower_threshold: int,
    upper_threshold: int,
    efficiency: float = 1.0,
    dark_counts: float = 0.0,
) -> dict[str, float]:
    """
    Calculate analytical performance metrics for an equally likely
    binary PNR receiver with an erasure region.

    Decision rule:
        n <= lower_threshold -> 0
        lower_threshold < n < upper_threshold -> erasure
        n >= upper_threshold -> 1
    """

    if mu_0 < 0.0 or mu_1 < 0.0:
        raise ValueError("Mean photon numbers cannot be negative.")

    if lower_threshold < 0:
        raise ValueError("Lower threshold cannot be negative.")

    if upper_threshold <= lower_threshold:
        raise ValueError(
            "Upper threshold must be greater than the lower threshold."
        )

    if not 0.0 <= efficiency <= 1.0:
        raise ValueError("Efficiency must be between 0 and 1.")

    if dark_counts < 0.0:
        raise ValueError("Dark counts cannot be negative.")

    detected_mu_0 = efficiency * mu_0 + dark_counts
    detected_mu_1 = efficiency * mu_1 + dark_counts

    correct_given_0 = poisson.cdf(
        lower_threshold,
        detected_mu_0,
    )

    error_given_0 = 1.0 - poisson.cdf(
        upper_threshold - 1,
        detected_mu_0,
    )

    error_given_1 = poisson.cdf(
        lower_threshold,
        detected_mu_1,
    )

    correct_given_1 = 1.0 - poisson.cdf(
        upper_threshold - 1,
        detected_mu_1,
    )

    acceptance_probability = 0.5 * (
        correct_given_0
        + error_given_0
        + correct_given_1
        + error_given_1
    )

    erasure_probability = 1.0 - acceptance_probability

    unconditional_error_probability = 0.5 * (
        error_given_0
        + error_given_1
    )

    conditional_ber = (
        unconditional_error_probability
        / acceptance_probability
        if acceptance_probability > 0.0
        else float("nan")
    )

    return {
        "acceptance_probability": acceptance_probability,
        "erasure_probability": erasure_probability,
        "unconditional_error_probability": (
            unconditional_error_probability
        ),
        "conditional_ber": conditional_ber,
        "correct_given_0": correct_given_0,
        "error_given_0": error_given_0,
        "correct_given_1": correct_given_1,
        "error_given_1": error_given_1,
    }