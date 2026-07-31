"""Validation of the ML nonlinearity-compensation layer.

On a nonlinear (Kerr phase) channel a learned equalizer must (a) improve on the
raw received symbols and (b) beat the best linear equalizer, which provably
cannot undo an intensity-dependent phase rotation.
"""

from __future__ import annotations

import numpy as np
import pytest

from iq4comm.ml import (
    make_dataset,
    LinearEqualizer,
    VolterraEqualizer,
    NeuralEqualizer,
    evm,
    symbol_ber,
)

FMT = "16QAM"


def _train_eval(EqClass, **kw):
    data = make_dataset(FMT, 20000, phi_nl=0.6, snr_db=25.0, seed=1)
    train, test = data.split(0.7)
    eq = EqClass(**kw).fit(train.rx, train.tx)
    est = eq.predict(test.rx)
    return {
        "evm_rx": evm(test.rx, test.tx),
        "evm_eq": evm(est, test.tx),
        "ber_rx": symbol_ber(test.rx, test.bits, FMT),
        "ber_eq": symbol_ber(est, test.bits, FMT),
        "ber_lin": symbol_ber(
            LinearEqualizer().fit(train.rx, train.tx).predict(test.rx),
            test.bits, FMT),
    }


def test_linear_equalizer_cannot_beat_raw_much():
    """A purely linear equalizer barely helps against a nonlinear phase."""
    r = _train_eval(LinearEqualizer)
    # Linear EQ leaves substantial error (it cannot undo intensity-dependent phase).
    assert r["ber_eq"] > 1e-3


def test_volterra_reduces_evm_and_ber():
    r = _train_eval(VolterraEqualizer, degree=3, alpha=1e-3)
    assert r["evm_eq"] < r["evm_rx"]          # improves on raw received
    assert r["ber_eq"] < r["ber_lin"]         # beats the linear baseline


def test_neural_reduces_evm_and_ber():
    r = _train_eval(NeuralEqualizer, hidden_layers=(48, 48), max_iter=800, seed=0)
    assert r["evm_eq"] < r["evm_rx"]
    assert r["ber_eq"] < r["ber_lin"]


def test_equalizer_api_shapes():
    data = make_dataset("QPSK", 2000, seed=3)
    eq = VolterraEqualizer().fit(data.rx, data.tx)
    out = eq.predict(data.rx)
    assert out.shape == data.tx.shape
    assert np.iscomplexobj(out)
