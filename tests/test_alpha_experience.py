from __future__ import annotations

import runpy
try:
    import tomllib
except ModuleNotFoundError:  # Python 3.10
    import tomli as tomllib
from pathlib import Path

import pytest

from iq4comm.analysis.receiver_family import (
    ReceiverFamilyConfiguration,
    build_argument_parser,
    compare_receiver_families,
    format_receiver_family_report,
    generate_heterodyne_candidates,
    generate_homodyne_candidates,
    generate_pnr_candidates,
    main as receiver_family_main,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def reduced_configuration() -> ReceiverFamilyConfiguration:
    return ReceiverFamilyConfiguration(
        distances_km=(0.0, 20.0),
        max_pnr_threshold=10,
        homodyne_threshold_step=0.25,
        heterodyne_threshold_step=0.25,
    )


def test_receiver_family_configuration_normalizes_and_validates() -> None:
    config = ReceiverFamilyConfiguration(distances_km=[0, 10, 20])
    assert config.distances_km == (0.0, 10.0, 20.0)

    with pytest.raises(ValueError, match="mu_1"):
        ReceiverFamilyConfiguration(mu_0=2.0, mu_1=2.0)
    with pytest.raises(ValueError, match="Distances"):
        ReceiverFamilyConfiguration(distances_km=(0.0, -1.0))
    with pytest.raises(ValueError, match="threshold_step"):
        ReceiverFamilyConfiguration(homodyne_threshold_step=0.0)


def test_receiver_family_candidate_generators_cover_ordered_pairs() -> None:
    assert len(list(generate_pnr_candidates(4, 1.0, 0.0))) == 10
    assert len(
        list(generate_homodyne_candidates(0.0, 1.0, 0.5, 1.0, 0.0))
    ) == 3
    assert len(
        list(generate_heterodyne_candidates(0.0, 1.0, 0.5, 1.0, 0.0))
    ) == 3


def test_receiver_family_comparison_regression() -> None:
    rows = compare_receiver_families(reduced_configuration())

    assert [row.distance_km for row in rows] == [0.0, 20.0]
    assert [row.winner for row in rows] == ["PNR", "Homodyne"]
    assert rows[0].pnr.metrics.conditional_ber == pytest.approx(
        0.020001594989548087
    )
    assert rows[1].homodyne.metrics.conditional_ber == pytest.approx(
        0.13159737494330598
    )
    assert rows[0].pnr.receiver.lower_threshold == 2
    assert rows[0].pnr.receiver.upper_threshold == 6


def test_receiver_family_results_respect_acceptance_constraint() -> None:
    config = reduced_configuration()
    rows = compare_receiver_families(config)

    for row in rows:
        assert row.transmittance > 0.0
        assert row.received_mu_1 > row.received_mu_0
        for result in row.results.values():
            assert result.metrics.acceptance_probability >= config.minimum_acceptance


def test_receiver_family_report_is_branded_and_complete() -> None:
    config = reduced_configuration()
    report = format_receiver_family_report(
        compare_receiver_families(config),
        config,
    )

    assert report.startswith("iQuant4Comm Receiver-Family Comparison")
    assert "PNR thresholds" in report
    assert "Hom thresholds" in report
    assert "Het thresholds" in report
    assert "      0.0" in report
    assert "     20.0" in report


def test_receiver_family_cli_parser_accepts_public_options() -> None:
    args = build_argument_parser().parse_args(
        [
            "--mu0",
            "1.0",
            "--mu1",
            "4.0",
            "--distances",
            "0",
            "25",
            "--threshold-step",
            "0.2",
        ]
    )

    assert args.mu0 == pytest.approx(1.0)
    assert args.mu1 == pytest.approx(4.0)
    assert args.distances == [0.0, 25.0]
    assert args.threshold_step == pytest.approx(0.2)


def test_receiver_family_main_prints_report(capsys: pytest.CaptureFixture[str]) -> None:
    receiver_family_main(
        [
            "--distances",
            "0",
            "--threshold-step",
            "0.5",
            "--max-pnr-threshold",
            "8",
        ]
    )

    output = capsys.readouterr().out
    assert "iQuant4Comm Receiver-Family Comparison" in output
    assert "Winner" in output


def test_alpha_quickstart_runs_headlessly(capsys: pytest.CaptureFixture[str]) -> None:
    runpy.run_path(
        str(PROJECT_ROOT / "examples" / "alpha_quickstart.py"),
        run_name="__main__",
    )

    output = capsys.readouterr().out
    assert "iQuant4 alpha version: 0.2.0a1" in output
    assert "Wigner normalization:" in output
    assert "20 km PNR conditional BER:" in output


def test_distribution_declares_receiver_family_console_script() -> None:
    metadata = tomllib.loads(
        (PROJECT_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    )

    assert metadata["project"]["scripts"]["iq4comm-receiver-family"] == (
        "iq4comm.analysis.receiver_family:main"
    )


def test_legacy_main_delegates_to_canonical_entry_point() -> None:
    import main as legacy_main

    assert legacy_main.main is receiver_family_main
