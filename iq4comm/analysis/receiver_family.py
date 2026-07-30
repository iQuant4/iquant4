"""Receiver-family optimization and comparison utilities.

This module turns the original receiver comparison script into a reusable,
testable API. It compares erasure PNR, homodyne, and heterodyne receivers under
a common minimum-acceptance constraint.
"""

from __future__ import annotations

import argparse
from collections.abc import Iterator, Sequence
from dataclasses import dataclass

import numpy as np

from ..channels.fiber import FiberChannel
from ..models.channel_state import ChannelState
from ..optimization.receiver import OptimizationResult, optimize_receiver
from ..receivers.heterodyne import ErasureHeterodyneReceiver
from ..receivers.homodyne import ErasureHomodyneReceiver
from ..receivers.pnr import ErasurePNRReceiver
from ..sources.coherent import BinaryCoherentSource


_RECEIVER_NAMES = ("PNR", "Homodyne", "Heterodyne")


@dataclass(frozen=True, slots=True)
class ReceiverFamilyConfiguration:
    """Configuration for a receiver-family comparison experiment."""

    mu_0: float = 2.0
    mu_1: float = 8.0
    attenuation_db_per_km: float = 0.2
    distances_km: tuple[float, ...] = (
        0.0,
        10.0,
        20.0,
        30.0,
        40.0,
        50.0,
        60.0,
        70.0,
        80.0,
    )
    minimum_acceptance: float = 0.75
    pnr_efficiency: float = 1.0
    dark_counts: float = 0.0
    max_pnr_threshold: int = 20
    homodyne_efficiency: float = 1.0
    homodyne_excess_noise_variance: float = 0.0
    homodyne_threshold_step: float = 0.05
    heterodyne_efficiency: float = 1.0
    heterodyne_excess_noise_variance: float = 0.0
    heterodyne_threshold_step: float = 0.05

    def __post_init__(self) -> None:
        distances = tuple(float(value) for value in self.distances_km)
        object.__setattr__(self, "distances_km", distances)

        if self.mu_0 < 0.0 or self.mu_1 < 0.0:
            raise ValueError("Mean photon numbers cannot be negative.")
        if self.mu_1 <= self.mu_0:
            raise ValueError("mu_1 must be greater than mu_0.")
        if self.attenuation_db_per_km < 0.0:
            raise ValueError("Fiber attenuation cannot be negative.")
        if not distances:
            raise ValueError("At least one distance is required.")
        if any(distance < 0.0 for distance in distances):
            raise ValueError("Distances cannot be negative.")
        if not 0.0 <= self.minimum_acceptance <= 1.0:
            raise ValueError("minimum_acceptance must be between 0 and 1.")

        efficiencies = (
            self.pnr_efficiency,
            self.homodyne_efficiency,
            self.heterodyne_efficiency,
        )
        if any(not 0.0 <= value <= 1.0 for value in efficiencies):
            raise ValueError("Receiver efficiencies must be between 0 and 1.")
        if self.dark_counts < 0.0:
            raise ValueError("Dark counts cannot be negative.")
        if self.max_pnr_threshold < 1:
            raise ValueError("max_pnr_threshold must be at least 1.")

        noise_variances = (
            self.homodyne_excess_noise_variance,
            self.heterodyne_excess_noise_variance,
        )
        if any(value < 0.0 for value in noise_variances):
            raise ValueError("Excess-noise variances cannot be negative.")
        if self.homodyne_threshold_step <= 0.0:
            raise ValueError("homodyne_threshold_step must be positive.")
        if self.heterodyne_threshold_step <= 0.0:
            raise ValueError("heterodyne_threshold_step must be positive.")


@dataclass(frozen=True, slots=True)
class ReceiverFamilyRow:
    """Optimized receiver results at one propagation distance."""

    distance_km: float
    transmittance: float
    received_mu_0: float
    received_mu_1: float
    pnr: OptimizationResult
    homodyne: OptimizationResult
    heterodyne: OptimizationResult
    winner: str

    def __post_init__(self) -> None:
        if self.winner not in _RECEIVER_NAMES:
            raise ValueError(f"Unknown receiver-family winner: {self.winner}")

    @property
    def results(self) -> dict[str, OptimizationResult]:
        """Return results keyed by receiver-family name."""
        return {
            "PNR": self.pnr,
            "Homodyne": self.homodyne,
            "Heterodyne": self.heterodyne,
        }



def generate_pnr_candidates(
    max_threshold: int,
    efficiency: float,
    dark_counts: float,
) -> Iterator[ErasurePNRReceiver]:
    """Yield all ordered PNR erasure-threshold pairs."""
    for lower_threshold in range(max_threshold):
        for upper_threshold in range(lower_threshold + 1, max_threshold + 1):
            yield ErasurePNRReceiver(
                lower_threshold=lower_threshold,
                upper_threshold=upper_threshold,
                efficiency=efficiency,
                dark_counts=dark_counts,
            )



def _threshold_values(
    minimum_threshold: float,
    maximum_threshold: float,
    threshold_step: float,
) -> np.ndarray:
    if threshold_step <= 0.0:
        raise ValueError("threshold_step must be positive.")
    if maximum_threshold <= minimum_threshold:
        raise ValueError("maximum_threshold must exceed minimum_threshold.")

    return np.arange(
        minimum_threshold,
        maximum_threshold + 0.5 * threshold_step,
        threshold_step,
        dtype=float,
    )



def generate_homodyne_candidates(
    minimum_threshold: float,
    maximum_threshold: float,
    threshold_step: float,
    efficiency: float,
    excess_noise_variance: float,
) -> Iterator[ErasureHomodyneReceiver]:
    """Yield homodyne erasure receivers over a threshold grid."""
    threshold_values = _threshold_values(
        minimum_threshold,
        maximum_threshold,
        threshold_step,
    )

    for lower_threshold in threshold_values:
        for upper_threshold in threshold_values:
            if upper_threshold <= lower_threshold:
                continue
            yield ErasureHomodyneReceiver(
                lower_threshold=float(lower_threshold),
                upper_threshold=float(upper_threshold),
                efficiency=efficiency,
                excess_noise_variance=excess_noise_variance,
            )



def generate_heterodyne_candidates(
    minimum_threshold: float,
    maximum_threshold: float,
    threshold_step: float,
    efficiency: float,
    excess_noise_variance: float,
) -> Iterator[ErasureHeterodyneReceiver]:
    """Yield heterodyne erasure receivers over a threshold grid."""
    threshold_values = _threshold_values(
        minimum_threshold,
        maximum_threshold,
        threshold_step,
    )

    for lower_threshold in threshold_values:
        for upper_threshold in threshold_values:
            if upper_threshold <= lower_threshold:
                continue
            yield ErasureHeterodyneReceiver(
                lower_threshold=float(lower_threshold),
                upper_threshold=float(upper_threshold),
                efficiency=efficiency,
                excess_noise_variance=excess_noise_variance,
            )



def optimize_pnr_family(
    state_0: ChannelState,
    state_1: ChannelState,
    minimum_acceptance: float,
    efficiency: float,
    dark_counts: float,
    max_threshold: int,
) -> OptimizationResult:
    """Optimize the erasure-PNR receiver family."""
    return optimize_receiver(
        candidates=generate_pnr_candidates(
            max_threshold=max_threshold,
            efficiency=efficiency,
            dark_counts=dark_counts,
        ),
        state_0=state_0,
        state_1=state_1,
        minimum_acceptance=minimum_acceptance,
    )



def optimize_homodyne_family(
    state_0: ChannelState,
    state_1: ChannelState,
    minimum_acceptance: float,
    efficiency: float,
    excess_noise_variance: float,
    threshold_step: float,
) -> OptimizationResult:
    """Optimize the erasure-homodyne receiver family."""
    mean_0 = np.sqrt(2.0 * efficiency) * np.real(state_0.alpha)
    mean_1 = np.sqrt(2.0 * efficiency) * np.real(state_1.alpha)
    standard_deviation = np.sqrt(0.5 + excess_noise_variance)
    margin = 4.0 * standard_deviation

    return optimize_receiver(
        candidates=generate_homodyne_candidates(
            minimum_threshold=mean_0 - margin,
            maximum_threshold=mean_1 + margin,
            threshold_step=threshold_step,
            efficiency=efficiency,
            excess_noise_variance=excess_noise_variance,
        ),
        state_0=state_0,
        state_1=state_1,
        minimum_acceptance=minimum_acceptance,
    )



def optimize_heterodyne_family(
    state_0: ChannelState,
    state_1: ChannelState,
    minimum_acceptance: float,
    efficiency: float,
    excess_noise_variance: float,
    threshold_step: float,
) -> OptimizationResult:
    """Optimize the erasure-heterodyne receiver family."""
    mean_0 = np.sqrt(efficiency) * np.real(state_0.alpha)
    mean_1 = np.sqrt(efficiency) * np.real(state_1.alpha)
    standard_deviation = np.sqrt(0.5 + excess_noise_variance)
    margin = 4.0 * standard_deviation

    return optimize_receiver(
        candidates=generate_heterodyne_candidates(
            minimum_threshold=mean_0 - margin,
            maximum_threshold=mean_1 + margin,
            threshold_step=threshold_step,
            efficiency=efficiency,
            excess_noise_variance=excess_noise_variance,
        ),
        state_0=state_0,
        state_1=state_1,
        minimum_acceptance=minimum_acceptance,
    )



def compare_receiver_families(
    configuration: ReceiverFamilyConfiguration | None = None,
) -> tuple[ReceiverFamilyRow, ...]:
    """Optimize PNR, homodyne, and heterodyne families over distance."""
    config = configuration or ReceiverFamilyConfiguration()
    source = BinaryCoherentSource(mu_0=config.mu_0, mu_1=config.mu_1)
    channel = FiberChannel(
        attenuation_db_per_km=config.attenuation_db_per_km,
    )
    rows: list[ReceiverFamilyRow] = []

    for distance_km in config.distances_km:
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

        pnr_result = optimize_pnr_family(
            state_0=state_0,
            state_1=state_1,
            minimum_acceptance=config.minimum_acceptance,
            efficiency=config.pnr_efficiency,
            dark_counts=config.dark_counts,
            max_threshold=config.max_pnr_threshold,
        )
        homodyne_result = optimize_homodyne_family(
            state_0=state_0,
            state_1=state_1,
            minimum_acceptance=config.minimum_acceptance,
            efficiency=config.homodyne_efficiency,
            excess_noise_variance=config.homodyne_excess_noise_variance,
            threshold_step=config.homodyne_threshold_step,
        )
        heterodyne_result = optimize_heterodyne_family(
            state_0=state_0,
            state_1=state_1,
            minimum_acceptance=config.minimum_acceptance,
            efficiency=config.heterodyne_efficiency,
            excess_noise_variance=config.heterodyne_excess_noise_variance,
            threshold_step=config.heterodyne_threshold_step,
        )

        results = {
            "PNR": pnr_result,
            "Homodyne": homodyne_result,
            "Heterodyne": heterodyne_result,
        }
        winner = min(
            results,
            key=lambda name: results[name].metrics.conditional_ber,
        )

        rows.append(
            ReceiverFamilyRow(
                distance_km=distance_km,
                transmittance=state_0.transmittance,
                received_mu_0=state_0.mu,
                received_mu_1=state_1.mu,
                pnr=pnr_result,
                homodyne=homodyne_result,
                heterodyne=heterodyne_result,
                winner=winner,
            )
        )

    return tuple(rows)



def threshold_text(receiver: object) -> str:
    """Format an optimized erasure receiver's threshold pair."""
    if isinstance(receiver, ErasurePNRReceiver):
        return f"({receiver.lower_threshold},{receiver.upper_threshold})"

    lower_threshold = getattr(receiver, "lower_threshold")
    upper_threshold = getattr(receiver, "upper_threshold")
    return f"({lower_threshold:.2f},{upper_threshold:.2f})"



def format_receiver_family_report(
    rows: Sequence[ReceiverFamilyRow],
    configuration: ReceiverFamilyConfiguration | None = None,
) -> str:
    """Return a human-readable receiver-family comparison table."""
    config = configuration or ReceiverFamilyConfiguration()
    source = BinaryCoherentSource(mu_0=config.mu_0, mu_1=config.mu_1)
    channel = FiberChannel(
        attenuation_db_per_km=config.attenuation_db_per_km,
    )

    lines = [
        "iQuant4Comm Receiver-Family Comparison",
        "----------------------------------------",
        str(source),
        str(channel),
        f"Minimum acceptance C : {config.minimum_acceptance}",
        "",
    ]

    header = (
        f"{'Distance':>9}"
        f"{'PNR BER':>11}"
        f"{'Hom BER':>11}"
        f"{'Het BER':>11}"
        f"{'PNR thresholds':>18}"
        f"{'Hom thresholds':>20}"
        f"{'Het thresholds':>20}"
        f"{'Winner':>12}"
    )
    lines.extend((header, "-" * len(header)))

    for row in rows:
        lines.append(
            f"{row.distance_km:>9.1f}"
            f"{row.pnr.metrics.conditional_ber:>11.6f}"
            f"{row.homodyne.metrics.conditional_ber:>11.6f}"
            f"{row.heterodyne.metrics.conditional_ber:>11.6f}"
            f"{threshold_text(row.pnr.receiver):>18}"
            f"{threshold_text(row.homodyne.receiver):>20}"
            f"{threshold_text(row.heterodyne.receiver):>20}"
            f"{row.winner:>12}"
        )

    return "\n".join(lines)



def build_argument_parser() -> argparse.ArgumentParser:
    """Build the command-line parser for the receiver-family demo."""
    parser = argparse.ArgumentParser(
        prog="iq4comm-receiver-family",
        description=(
            "Compare optimized erasure PNR, homodyne, and heterodyne "
            "receivers over a pure-loss fiber link."
        ),
    )
    parser.add_argument("--mu0", type=float, default=2.0)
    parser.add_argument("--mu1", type=float, default=8.0)
    parser.add_argument("--attenuation", type=float, default=0.2)
    parser.add_argument(
        "--distances",
        type=float,
        nargs="+",
        default=list(ReceiverFamilyConfiguration().distances_km),
    )
    parser.add_argument("--minimum-acceptance", type=float, default=0.75)
    parser.add_argument("--threshold-step", type=float, default=0.05)
    parser.add_argument("--max-pnr-threshold", type=int, default=20)
    return parser



def main(argv: Sequence[str] | None = None) -> None:
    """Run the receiver-family comparison command-line application."""
    args = build_argument_parser().parse_args(argv)
    config = ReceiverFamilyConfiguration(
        mu_0=args.mu0,
        mu_1=args.mu1,
        attenuation_db_per_km=args.attenuation,
        distances_km=tuple(args.distances),
        minimum_acceptance=args.minimum_acceptance,
        max_pnr_threshold=args.max_pnr_threshold,
        homodyne_threshold_step=args.threshold_step,
        heterodyne_threshold_step=args.threshold_step,
    )
    rows = compare_receiver_families(config)
    print(format_receiver_family_report(rows, config))


__all__ = [
    "ReceiverFamilyConfiguration",
    "ReceiverFamilyRow",
    "build_argument_parser",
    "compare_receiver_families",
    "format_receiver_family_report",
    "generate_heterodyne_candidates",
    "generate_homodyne_candidates",
    "generate_pnr_candidates",
    "main",
    "optimize_heterodyne_family",
    "optimize_homodyne_family",
    "optimize_pnr_family",
    "threshold_text",
]


if __name__ == "__main__":
    main()
