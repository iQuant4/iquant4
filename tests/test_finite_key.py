"""Regression tests for the finite-key sensitivity estimate."""

from __future__ import annotations

import numpy as np
import pytest

from iqcore.fiber import SMF28
from iq4comm.qkd import (
    FiniteKeyParams,
    finite_key_fraction,
    bb84_decoy_key_rate,
    tf_qkd_key_rate,
    cvqkd_homodyne_key_rate,
    cvqkd_rate_vs_distance,
)

GAIN, ERROR = 1e-3, 0.03


def test_finite_converges_to_asymptotic():
    asym = finite_key_fraction(GAIN, ERROR)
    huge = finite_key_fraction(GAIN, ERROR, params=FiniteKeyParams(1e14, 1e-9))
    assert huge == pytest.approx(asym, rel=1e-2)


def test_finite_is_below_asymptotic_and_monotonic_in_N():
    asym = finite_key_fraction(GAIN, ERROR)
    big = finite_key_fraction(GAIN, ERROR, params=FiniteKeyParams(1e11, 1e-9))
    small = finite_key_fraction(GAIN, ERROR, params=FiniteKeyParams(1e8, 1e-9))
    assert big < asym
    assert small < big
    # A too-small block yields no secure key.
    assert finite_key_fraction(GAIN, ERROR, params=FiniteKeyParams(1e5, 1e-9)) == 0.0


def test_bb84_finite_reach_shrinks_with_block_size():
    d = np.arange(0, 260, 1.0)
    def reach(N):
        fp = None if N is None else FiniteKeyParams(N, 1e-9)
        r = np.array([bb84_decoy_key_rate(SMF28.transmissivity(x), finite=fp) for x in d])
        return d[np.max(np.where(r > 0))]
    r_inf = reach(None)
    r_10 = reach(1e10)
    r_8 = reach(1e8)
    r_7 = reach(1e7)
    assert r_inf >= r_10 > r_8 > r_7            # shorter block -> shorter reach
    assert r_7 > 0                               # still works at short range


def test_bb84_finite_never_exceeds_asymptotic():
    for dkm in (0.0, 50.0, 100.0, 150.0):
        eta = SMF28.transmissivity(dkm)
        a = bb84_decoy_key_rate(eta)
        f = bb84_decoy_key_rate(eta, finite=FiniteKeyParams(1e9, 1e-9))
        assert f <= a + 1e-12


def test_tf_finite_key_supported():
    eta = SMF28.transmissivity(200.0)
    a = tf_qkd_key_rate(eta)
    f = tf_qkd_key_rate(eta, finite=FiniteKeyParams(1e11, 1e-9))
    assert 0.0 <= f <= a + 1e-12


def test_cv_finite_converges_and_reduces():
    t = SMF28.transmissivity(40.0)
    asym = cvqkd_homodyne_key_rate(t)
    huge = cvqkd_homodyne_key_rate(t, finite=FiniteKeyParams(1e14, 1e-9))
    small = cvqkd_homodyne_key_rate(t, finite=FiniteKeyParams(1e8, 1e-9))
    assert huge == pytest.approx(asym, rel=1e-2)     # -> asymptotic as N grows
    assert 0.0 <= small < asym                       # finite penalty


def test_cv_finite_reach_shrinks_with_block_size():
    d = np.arange(0, 360, 2.0)
    def reach(N):
        fp = None if N is None else FiniteKeyParams(N, 1e-9)
        r = cvqkd_rate_vs_distance(d, finite=fp)
        return d[np.max(np.where(r > 0))]
    assert reach(None) > reach(1e12) > reach(1e10) > reach(1e8) > 0


def test_finite_params_validation():
    with pytest.raises(ValueError):
        FiniteKeyParams(block_size=-1)
    with pytest.raises(ValueError):
        FiniteKeyParams(eps_security=2.0)
