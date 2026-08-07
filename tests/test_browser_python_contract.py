"""Parity tests for the offline explorer's JavaScript physics contract."""

from __future__ import annotations

import json
from pathlib import Path
import shutil
import subprocess

import pytest

from iqcore.fiber import Lightpath, SMF28, WSSFilter
from iq4comm.dsp.fec import get_fec_code
from iq4comm.dsp.pulse_shaping import PulseShape
from iq4comm.qkd import (
    RamanModel,
    raman_background_yield,
    raman_path_integral_km,
    system_key_rate,
    system_operating_point,
)
from iq4comm.qkd.format_impact import channel_snr_db


_NODE = shutil.which("node")
_CONTRACT = (
    Path(__file__).resolve().parents[1] / "explorer" / "physics_contract.js"
)


pytestmark = pytest.mark.skipif(_NODE is None, reason="Node.js is unavailable")


def _javascript(expression: str, payload: dict) -> object:
    script = (
        f"const p=require({json.dumps(str(_CONTRACT))});"
        f"const x={json.dumps(payload)};"
        f"process.stdout.write(JSON.stringify({expression}));"
    )
    completed = subprocess.run(
        [_NODE, "-e", script],
        check=True,
        capture_output=True,
        text=True,
    )
    return json.loads(completed.stdout)


@pytest.mark.parametrize(
    ("distance", "pump_loss", "quantum_loss", "direction"),
    [
        (60.0, 0.2, 0.2, "co"),
        (73.0, 0.19, 0.32, "co"),
        (73.0, 0.19, 0.32, "counter"),
        (100.0, 0.2000000001, 0.2, "co"),
    ],
)
def test_raman_path_integral_matches_python(
    distance: float, pump_loss: float, quantum_loss: float, direction: str
) -> None:
    browser = _javascript(
        "p.ramanPathIntegralKm(x.distanceKm,x.options)",
        {
            "distanceKm": distance,
            "options": {
                "pumpAttenuationDbPerKm": pump_loss,
                "quantumAttenuationDbPerKm": quantum_loss,
                "propagationDirection": direction,
            },
        },
    )
    python = raman_path_integral_km(
        distance,
        pump_attenuation_db_per_km=pump_loss,
        quantum_attenuation_db_per_km=quantum_loss,
        propagation_direction=direction,
    )
    assert browser == pytest.approx(python, rel=2e-14, abs=1e-15)


def test_raman_background_matches_python() -> None:
    payload = {
        "classicalTotalPowerW": 3.7e-3,
        "distanceKm": 68.0,
        "pumpAttenuationDbPerKm": 0.19,
        "quantumAttenuationDbPerKm": 0.31,
        "propagationDirection": "counter",
        "ramanCoefficientPerKmPerNm": 8.2e-10,
        "filterBandwidthNm": 0.043,
        "gateTimeS": 2.5e-9,
        "quantumWavelengthNm": 1310.0,
        "detectorEfficiency": 0.27,
    }
    browser = _javascript("p.ramanBackgroundYield(x)", payload)
    fiber = type(SMF28)(
        attenuation_db_per_km=payload["quantumAttenuationDbPerKm"],
        dispersion_ps_nm_km=SMF28.dispersion_ps_nm_km,
        dispersion_slope_ps_nm2_km=SMF28.dispersion_slope_ps_nm2_km,
        gamma_per_w_per_km=SMF28.gamma_per_w_per_km,
        reference_wavelength_nm=payload["quantumWavelengthNm"],
        core_area_um2=SMF28.core_area_um2,
        name="contract",
    )
    raman = RamanModel(
        raman_coeff_per_km_per_nm=payload["ramanCoefficientPerKmPerNm"],
        filter_bandwidth_nm=payload["filterBandwidthNm"],
        gate_time_s=payload["gateTimeS"],
        quantum_wavelength_nm=payload["quantumWavelengthNm"],
        propagation_direction=payload["propagationDirection"],
        pump_attenuation_db_per_km=payload["pumpAttenuationDbPerKm"],
    )
    python = raman_background_yield(
        payload["classicalTotalPowerW"],
        payload["distanceKm"],
        fiber=fiber,
        raman=raman,
        detector_efficiency=payload["detectorEfficiency"],
    )
    assert browser == pytest.approx(python, rel=2e-14)


@pytest.mark.parametrize("n_roadms", [1, 2, 3, 8])
def test_wss_loss_and_narrowing_match_python(n_roadms: int) -> None:
    occupied = 32e9 * 1.35
    browser = _javascript(
        "({loss:p.roadmInsertionLossDb(x.n),"
        "penalty:p.wssNarrowingPenaltyDb(p.roadmFilterStages(x.n),x.bw)})",
        {"n": n_roadms, "bw": occupied},
    )
    lightpath = Lightpath(n_roadms, WSSFilter())
    assert browser["loss"] == pytest.approx(lightpath.insertion_loss_db)
    assert browser["penalty"] == pytest.approx(
        lightpath.narrowing_penalty_db(occupied), rel=2e-13)


def test_gn_channel_snr_matches_python() -> None:
    payload = {
        "launchDbmPerChannel": -3.2,
        "channelCount": 48,
        "distanceKm": 77.0,
        "channelSpacingHz": 39.2e9,
    }
    browser = _javascript("p.channelSnrDb(x)", payload)
    python = channel_snr_db(
        payload["launchDbmPerChannel"],
        payload["channelCount"],
        payload["distanceKm"],
        channel_spacing_hz=payload["channelSpacingHz"],
    )
    assert browser == pytest.approx(python, rel=2e-14)


def test_complete_dv_operating_point_matches_python() -> None:
    payload = {
        "distanceKm": 55.0,
        "launchDbmPerChannel": -5.0,
        "channelCount": 32,
        "rolloff": 0.25,
        "nRoadms": 3,
        "format": "16QAM",
        "fec": "HD-FEC-7%",
        "protocol": "dv",
    }
    browser = _javascript("p.systemOperatingPoint(x)", payload)
    python = system_operating_point(
        payload["distanceKm"],
        payload["channelCount"],
        payload["launchDbmPerChannel"],
        fmt=payload["format"],
        pulse=PulseShape("rrc", payload["rolloff"]),
        fec=get_fec_code(payload["fec"]),
        n_roadms=payload["nRoadms"],
        qkd_protocol="dv",
    )
    assert browser["capacityBps"] == pytest.approx(python.classical_capacity_bps)
    assert browser["closes"] is python.classical_closes
    assert browser["roadmLossDb"] == pytest.approx(python.roadm_loss_db)
    assert browser["keyRate"] == pytest.approx(python.secret_key_rate, rel=2e-13)
    assert browser["modelStatus"] == python.qkd_model_status.value
    assert browser["recommendationEligible"] is True


def test_tf_browser_result_is_labelled_and_matches_opted_in_python_proxy() -> None:
    payload = {
        "distanceKm": 150.0,
        "launchDbmPerChannel": -8.0,
        "channelCount": 20,
        "nRoadms": 0,
        "protocol": "tf",
    }
    browser = _javascript(
        "({rate:p.systemKeyRate(x),status:p.systemOperatingPoint({"
        "...x,rolloff:.2,format:'QPSK',fec:'none'}).modelStatus,"
        "eligible:p.systemOperatingPoint({"
        "...x,rolloff:.2,format:'QPSK',fec:'none'}).recommendationEligible})",
        payload,
    )
    python = system_key_rate(
        "tf",
        payload["distanceKm"],
        payload["launchDbmPerChannel"],
        payload["channelCount"],
        allow_scaling_proxy=True,
    )
    assert browser["rate"] == pytest.approx(python, rel=2e-13)
    assert browser["status"] == "scaling_proxy"
    assert browser["eligible"] is False
