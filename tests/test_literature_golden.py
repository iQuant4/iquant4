"""Locked comparisons with independently published experimental data."""

from __future__ import annotations

from dataclasses import replace
import json
from pathlib import Path

import numpy as np
import pytest

from iqcore.fiber import SMF28
from iq4comm.qkd import RamanModel, raman_background_yield


_GOLDEN = (
    Path(__file__).resolve().parents[1]
    / "validation"
    / "golden"
    / "raman_da_silva_2014.json"
)


@pytest.fixture(scope="module")
def da_silva_config_g() -> dict:
    return json.loads(_GOLDEN.read_text(encoding="utf-8"))


@pytest.mark.parametrize("direction", ["co", "counter"])
def test_raman_distance_law_reproduces_locked_literature_series(
    da_silva_config_g: dict, direction: str
) -> None:
    """The implementation follows all six published distance points."""
    config = da_silva_config_g["configuration"]
    series = da_silva_config_g["series"][direction]
    fit = series["frozen_fit"]
    attenuation = fit["attenuation_db_per_km"]
    fiber = replace(SMF28, attenuation_db_per_km=attenuation)
    raman = RamanModel(
        raman_coeff_per_km_per_nm=fit["effective_rho_per_km_per_nm"],
        filter_bandwidth_nm=config["filter_bandwidth_nm_at_quantum_wavelength"],
        gate_time_s=config["gate_time_s"],
        quantum_wavelength_nm=config["quantum_wavelength_nm"],
        propagation_direction=direction,
        pump_attenuation_db_per_km=attenuation,
    )
    launch_w = (
        config["classical_channel_count"]
        * 1e-3
        * 10.0 ** (config["launch_power_dbm_per_channel"] / 10.0)
    )
    calculated = np.asarray([
        raman_background_yield(
            launch_w,
            distance,
            fiber=fiber,
            raman=raman,
            detector_efficiency=config["detector_efficiency"],
        )
        for distance in series["distance_km"]
    ])
    observed = np.asarray(series["counts_per_trigger"])
    point_errors = np.abs(calculated - observed) / observed
    assert point_errors.max() <= fit["max_allowed_relative_point_error"]


def test_golden_dataset_records_axis_multiplier(da_silva_config_g: dict) -> None:
    """Guard specifically against the historical x10^-4 transcription error."""
    assert da_silva_config_g["extraction"]["axis_multiplier"] == 1e-4
    assert max(da_silva_config_g["series"]["co"]["counts_per_trigger"]) < 1e-3
