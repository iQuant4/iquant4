"""Validation of the WSS / ROADM wavelength-routing model."""

from __future__ import annotations

import numpy as np
import pytest

from iqcore.fiber import (
    WSSFilter,
    cascaded_bandwidth_3db_ghz,
    filter_narrowing_penalty_db,
    Roadm,
    Lightpath,
    lightpath_penalty_db,
    WDMChannel,
    WDMComb,
    DWDMGrid,
)


def test_super_gaussian_minus_3db_at_half_bandwidth():
    """Transmission is exactly −3 dB at df = B_3dB/2, for any order."""
    for order in (1, 2, 3, 4):
        wss = WSSFilter(bandwidth_3db_ghz=40.0, order=order)
        edge = 20e9                                     # B/2
        assert wss.transfer(edge) == pytest.approx(0.5, rel=1e-9)
        assert wss.transfer(0.0) == pytest.approx(1.0)


def test_higher_order_is_flatter_in_band_and_steeper_out():
    """A higher-order super-Gaussian passes more in-band, rejects more out-of-band."""
    lo = WSSFilter(40.0, order=1)
    hi = WSSFilter(40.0, order=4)
    assert hi.transfer(8e9) > lo.transfer(8e9)          # flatter near centre
    assert hi.transfer(30e9) < lo.transfer(30e9)         # steeper skirt


def test_cascade_narrows_passband():
    wss = WSSFilter(40.0, order=3)
    b1 = cascaded_bandwidth_3db_ghz(wss, 1)
    b5 = cascaded_bandwidth_3db_ghz(wss, 5)
    b10 = cascaded_bandwidth_3db_ghz(wss, 10)
    assert b1 == pytest.approx(40.0)
    assert b5 < b1 and b10 < b5                          # monotone narrowing
    assert b5 == pytest.approx(40.0 * (1 / 5) ** (1 / 6), rel=1e-9)


def test_narrowing_penalty_grows_with_nodes_and_rolloff():
    wss = WSSFilter(50.0, order=3)
    rs = 32e9
    bw_narrow = rs * 1.05                                # beta=0.05
    bw_wide = rs * 1.5                                   # beta=0.5
    p1 = filter_narrowing_penalty_db(wss, 1, bw_narrow)
    p8 = filter_narrowing_penalty_db(wss, 8, bw_narrow)
    assert p8 > p1 >= 0                                  # more nodes -> more penalty
    # wider signal is clipped more at the same node count
    assert filter_narrowing_penalty_db(wss, 8, bw_wide) > filter_narrowing_penalty_db(wss, 8, bw_narrow)


def test_roadm_express_drop_add_conserves_and_attenuates():
    grid = DWDMGrid(spacing_ghz=50.0)
    comb = WDMComb.uniform(grid, 0, 4, power_dbm_per_channel=0.0)   # 5 channels (0..4), 1 mW each
    roadm = Roadm(WSSFilter(50.0, order=3, insertion_loss_db=5.0))
    add = (WDMChannel(frequency_hz=grid.frequency_hz(10), power_w=1e-3),)
    res = roadm.route(comb, drop_indices=(1,), add_channels=add)
    assert res.dropped.num_channels == 1                            # one dropped
    assert res.express.num_channels == 5                            # 4 express + 1 add
    # express (through) channels attenuated by 2x insertion loss (10 dB total)
    through = [c for c in res.express.channels
               if c.frequency_hz != grid.frequency_hz(10)][0]
    assert through.power_dbm == pytest.approx(0.0 - 10.0, abs=1e-6)  # -10 dBm
    # the added channel took a single WSS stage (5 dB)
    added = [c for c in res.express.channels
             if c.frequency_hz == grid.frequency_hz(10)][0]
    assert added.power_dbm == pytest.approx(0.0 - 5.0, abs=1e-6)     # -5 dBm


def test_lightpath_insertion_loss_scales_with_nodes():
    wss = WSSFilter(50.0, order=3, insertion_loss_db=5.0)
    il2 = Lightpath(2, wss).insertion_loss_db
    il5 = Lightpath(5, wss).insertion_loss_db
    assert il5 > il2 > 0
    # 2 nodes = add + drop = 2 stages = 10 dB; 5 nodes = add+drop+3 express*2 = 8 stages
    assert il2 == pytest.approx(10.0)
    assert il5 == pytest.approx(8 * 5.0)


def test_lightpath_penalty_summary_and_fit_flag():
    rs = 32e9
    bw = rs * 1.1
    ok = lightpath_penalty_db(3, bw, wss=WSSFilter(50.0, order=3))
    tight = lightpath_penalty_db(20, bw, wss=WSSFilter(37.5, order=2))
    assert ok["signal_fits"] and ok["narrowing_penalty_db"] >= 0
    assert tight["effective_bandwidth_ghz"] < ok["effective_bandwidth_ghz"]
    assert tight["narrowing_penalty_db"] > ok["narrowing_penalty_db"]


def test_invalid_inputs_raise():
    with pytest.raises(ValueError):
        WSSFilter(bandwidth_3db_ghz=-1.0)
    with pytest.raises(ValueError):
        WSSFilter(40.0, order=0)
    with pytest.raises(ValueError):
        cascaded_bandwidth_3db_ghz(WSSFilter(40.0), 0)
