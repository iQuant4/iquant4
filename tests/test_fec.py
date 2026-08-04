"""Validation of the forward-error-correction / channel-coding module."""

from __future__ import annotations

import pytest

from iq4comm.dsp import (
    code_rate,
    overhead_percent,
    rs_post_decode_ber,
    rs_threshold_ber,
    required_ebn0_db,
    net_coding_gain_db,
    coded_net_bitrate_bps,
    get_fec_code,
    ber_theory,
    FEC_CODES,
)


def test_code_rate_and_overhead():
    assert code_rate(255, 239) == pytest.approx(239 / 255)
    assert overhead_percent(255, 239) == pytest.approx(100 * 16 / 239, rel=1e-6)
    with pytest.raises(ValueError):
        code_rate(200, 255)                       # k > n


def test_rs_post_decode_is_monotonic_and_waterfalls():
    """Post-FEC BER rises with channel BER and collapses far below threshold."""
    b = [1e-4, 5e-4, 1e-3, 5e-3, 1e-2]
    post = [rs_post_decode_ber(x, 255, 239) for x in b]
    assert all(y2 >= y1 for y1, y2 in zip(post, post[1:]))   # monotonic
    assert post[0] < 1e-10                                    # clean channel -> ~0 out
    assert post[-1] > post[0] * 1e6                           # steep waterfall


def test_rs_threshold_hits_target():
    """At the threshold BER the post-FEC BER equals the target."""
    target = 1e-12
    thr = rs_threshold_ber(255, 239, target_out_ber=target)
    assert 0 < thr < 1e-3
    assert rs_post_decode_ber(thr, 255, 239) == pytest.approx(target, rel=0.3)


def test_stronger_code_tolerates_worse_channel():
    """KP4 (more parity symbols) closes a noisier channel than RS(255,239)."""
    thr_rs = rs_threshold_ber(255, 239)
    thr_kp4 = get_fec_code("KP4").threshold_ber()
    assert thr_kp4 > thr_rs > 0


def test_required_ebn0_inverts_ber_theory():
    for fmt in ("QPSK", "16QAM"):
        for b in (1e-3, 1e-6, 1e-9):
            ebn0 = required_ebn0_db(fmt, b)
            assert ber_theory(fmt, ebn0) == pytest.approx(b, rel=0.05)


def test_net_coding_gain_positive_and_ordered():
    """Soft-decision 20% FEC gives more net coding gain than a weak RS code."""
    ncg_rs = net_coding_gain_db("QPSK", get_fec_code("RS(255,239)"))
    ncg_sd = net_coding_gain_db("QPSK", get_fec_code("SD-FEC-20%"))
    assert ncg_rs > 0
    assert ncg_sd > ncg_rs


def test_coded_net_bitrate_charges_overhead_and_gates_on_threshold():
    code = get_fec_code("SD-FEC-20%")            # threshold 2e-2
    raw = 100e9
    # Below threshold: link closes, net = raw * rate (overhead paid).
    good = coded_net_bitrate_bps(raw, code, 1e-2)
    assert good == pytest.approx(raw * code.rate)
    assert good < raw                             # 20% overhead really costs
    # Above threshold: link fails, no throughput.
    assert coded_net_bitrate_bps(raw, code, 5e-2) == 0.0


def test_hardcoded_platform_threshold_matches_a_real_code():
    """The 3.8e-3 '7% HD-FEC' constant used elsewhere is a real code's threshold."""
    assert get_fec_code("HD-FEC-7%").threshold_ber() == pytest.approx(3.8e-3)


def test_catalog_lookup_and_errors():
    assert set(FEC_CODES) >= {"RS(255,239)", "KP4", "HD-FEC-7%", "SD-FEC-20%"}
    with pytest.raises(ValueError):
        get_fec_code("nope")
    with pytest.raises(ValueError):
        rs_post_decode_ber(1e-3, 100, 200)        # n <= k
