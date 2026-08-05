"""Validation of the whole-system model: every knob -> both outputs."""

from __future__ import annotations

import pytest

from iqcore.fiber import WSSFilter
from iq4comm.dsp import PulseShape, get_fec_code
from iq4comm.qkd import (
    roadm_insertion_loss_db,
    system_key_rate,
    system_operating_point,
    protocol_coexistence_key_rate,
)


def test_no_roadm_matches_plain_coexistence():
    """With zero ROADMs the system key rate equals the plain coexistence rate."""
    d, p, n = 50.0, -12.0, 40
    a = system_key_rate("dv", d, p, n, n_roadms=0)
    b = protocol_coexistence_key_rate("dv", d, p, n)
    assert a == pytest.approx(b, rel=1e-9)


def test_roadm_loss_grows_with_nodes():
    assert roadm_insertion_loss_db(0) == 0.0
    l2 = roadm_insertion_loss_db(2)
    l6 = roadm_insertion_loss_db(6)
    assert l6 > l2 > 0


def test_more_roadms_lower_qkd_rate():
    """Each ROADM is pure loss on the quantum channel -> lower key rate.

    Uses a low-insertion-loss WSS and short reach so the degradation is graceful
    (with default 5 dB/WSS a few ROADMs already extinguish the quantum channel --
    itself the physical reason QKD does not route through many ROADMs).
    """
    d, p, n = 20.0, -18.0, 40
    wss = WSSFilter(insertion_loss_db=1.0)
    r0 = system_key_rate("dv", d, p, n, n_roadms=0, wss=wss)
    r2 = system_key_rate("dv", d, p, n, n_roadms=2, wss=wss)
    r4 = system_key_rate("dv", d, p, n, n_roadms=4, wss=wss)
    assert r0 > r2 > r4 > 0


def test_higher_launch_lowers_qkd_rate():
    """Raman rises with classical power, so QKD falls with launch power."""
    d, n = 40.0, 40
    hi = system_key_rate("dv", d, -8.0, n)
    lo = system_key_rate("dv", d, -18.0, n)
    assert lo > hi                              # less classical power -> more QKD


def test_cv_roadm_also_reduces_rate():
    d, p, n = 30.0, -16.0, 20
    r0 = system_key_rate("cv", d, p, n, n_roadms=0)
    r4 = system_key_rate("cv", d, p, n, n_roadms=4)
    assert r0 >= r4 >= 0
    assert r0 > 0


def test_system_operating_point_reports_both_outputs():
    op = system_operating_point(
        40.0, 40, -12.0, fmt="16QAM", pulse=PulseShape("rrc", 0.2),
        fec=get_fec_code("HD-FEC-7%"), n_roadms=3)
    assert op.channel_spacing_hz == pytest.approx(32e9 * 1.2)      # Rs(1+beta)
    assert op.roadm_loss_db > 0
    assert op.secret_key_rate >= 0
    assert op.fec_name == "HD-FEC 7% (staircase)"
    # capacity is charged the code overhead when it closes
    if op.classical_closes:
        assert op.classical_capacity_bps > 0


def test_roadm_narrowing_penalty_can_break_classical_link():
    """Many ROADMs + wide roll-off narrow the passband enough to drop capacity."""
    few = system_operating_point(40.0, 40, -10.0, fmt="16QAM",
                                 pulse=PulseShape("rrc", 0.5), n_roadms=1,
                                 wss=WSSFilter(37.5, order=2))
    many = system_operating_point(40.0, 40, -10.0, fmt="16QAM",
                                  pulse=PulseShape("rrc", 0.5), n_roadms=20,
                                  wss=WSSFilter(37.5, order=2))
    assert many.secret_key_rate <= few.secret_key_rate
    assert many.classical_capacity_bps <= few.classical_capacity_bps


def test_invalid_protocol_raises():
    with pytest.raises(ValueError):
        system_key_rate("nope", 40.0, -12.0, 40)
