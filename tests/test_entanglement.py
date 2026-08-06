"""Tests for entanglement distribution (BBM92, elementary-link fidelity)."""

from __future__ import annotations

import numpy as np
import pytest

from iqcore.fiber import SMF28
from iq4comm.qkd.dv import DetectorModel
from iq4comm.qkd.entanglement import (
    PairSource, heralded_g2, source_fidelity, coincidence_rate, coincidence_qber,
    elementary_link_fidelity, bbm92_key_rate, entanglement_reach_km, evaluate_link,
)
from iq4comm.qkd.repeater import chained_fidelity, werner_qber


def test_heralded_g2_and_multipair_fidelity():
    assert heralded_g2(0.01) == pytest.approx(0.02)
    # brighter source -> more multi-pairs -> lower emitted fidelity
    assert source_fidelity(PairSource(mean_pairs=0.2)) < source_fidelity(PairSource(mean_pairs=0.01))
    # zero brightness recovers the intrinsic fidelity
    assert source_fidelity(PairSource(mean_pairs=0.0, intrinsic_fidelity=0.98)) == pytest.approx(0.98)


def test_coincidence_rate_falls_with_distance():
    src = PairSource()
    rates = [coincidence_rate(L, source=src) for L in (0, 50, 100)]
    assert rates[0] > rates[1] > rates[2] > 0.0


def test_qber_to_fidelity_consistency():
    src = PairSource()
    e = coincidence_qber(30.0, source=src)
    F = elementary_link_fidelity(30.0, source=src)
    # F reproduces the QBER through the Werner relation
    assert werner_qber(F) == pytest.approx(e, abs=1e-9)


def test_bbm92_positive_then_vanishes_dark_limited():
    # dim source + high dark counts -> QBER-limited finite reach
    src = PairSource(mean_pairs=1e-3, pump_rate_hz=1e8)
    det = DetectorModel(efficiency=0.3, dark_count_prob=1e-4)
    assert bbm92_key_rate(0.0, source=src, detector=det) > 0.0
    reach = entanglement_reach_km(source=src, detector=det, max_km=400.0)
    assert 0.0 < reach < 400.0
    assert bbm92_key_rate(reach + 5.0, source=src, detector=det) == 0.0


def test_qber_rises_with_distance_when_dark_limited():
    src = PairSource(mean_pairs=1e-3, pump_rate_hz=1e8)
    det = DetectorModel(efficiency=0.3, dark_count_prob=1e-4)
    assert coincidence_qber(120.0, source=src, detector=det) > coincidence_qber(10.0, source=src, detector=det)


def test_elementary_fidelity_feeds_repeater():
    src = PairSource()
    F = elementary_link_fidelity(50.0, source=src)
    assert 0.5 < F <= 1.0
    # chaining reduces fidelity monotonically
    assert chained_fidelity(F, 3) < chained_fidelity(F, 2) < F


def test_evaluate_link_bundle():
    lk = evaluate_link(40.0)
    assert lk.coincidence_rate_hz > 0 and 0 <= lk.qber <= 0.5
    assert 0.25 <= lk.fidelity <= 1.0 and lk.bbm92_rate_bps >= 0.0
