"""Learned equalizers for nonlinearity compensation (numpy / scikit-learn).

Three equalizers with a common ``fit(rx, tx)`` / ``predict(rx)`` API, mapping
received complex symbols back toward the transmitted constellation:

* :class:`LinearEqualizer` -- best complex-affine fit ``a*rx + b`` (baseline;
  provably cannot undo an intensity-dependent phase rotation);
* :class:`VolterraEqualizer` -- polynomial (Volterra) features + ridge
  regression, the classic nonlinear equalizer;
* :class:`NeuralEqualizer` -- a small multilayer perceptron (scikit-learn), a
  learned nonlinear function.

These deliberately avoid a heavy autodiff dependency (PyTorch/JAX): they train
on CPU with scikit-learn, so the ML layer runs anywhere the rest of the platform
does.  A deep learned-DBP model is the natural next step once a GPU/torch
toolchain is in place.
"""

from __future__ import annotations

import numpy as np

__all__ = ["LinearEqualizer", "VolterraEqualizer", "NeuralEqualizer",
           "evm", "symbol_ber"]


def _feat(rx: np.ndarray) -> np.ndarray:
    return np.column_stack([rx.real, rx.imag])


def _targ(tx: np.ndarray) -> np.ndarray:
    return np.column_stack([tx.real, tx.imag])


def _cplx(y: np.ndarray) -> np.ndarray:
    return y[:, 0] + 1j * y[:, 1]


class LinearEqualizer:
    """Least-squares complex-affine equalizer ``y = a*rx + b`` (linear baseline)."""

    def fit(self, rx: np.ndarray, tx: np.ndarray) -> "LinearEqualizer":
        A = np.column_stack([rx, np.ones_like(rx)])
        coef, *_ = np.linalg.lstsq(A, tx, rcond=None)
        self.a, self.b = coef
        return self

    def predict(self, rx: np.ndarray) -> np.ndarray:
        return self.a * rx + self.b


class VolterraEqualizer:
    """Polynomial (Volterra) features + ridge regression."""

    def __init__(self, degree: int = 3, alpha: float = 1e-3) -> None:
        from sklearn.linear_model import Ridge
        from sklearn.pipeline import make_pipeline
        from sklearn.preprocessing import PolynomialFeatures
        self.model = make_pipeline(
            PolynomialFeatures(degree, include_bias=True),
            Ridge(alpha=alpha))

    def fit(self, rx: np.ndarray, tx: np.ndarray) -> "VolterraEqualizer":
        self.model.fit(_feat(rx), _targ(tx))
        return self

    def predict(self, rx: np.ndarray) -> np.ndarray:
        return _cplx(self.model.predict(_feat(rx)))


class NeuralEqualizer:
    """Small multilayer-perceptron equalizer (scikit-learn)."""

    def __init__(self, hidden_layers=(32, 32), alpha: float = 1e-4,
                 max_iter: int = 500, seed: int = 0) -> None:
        from sklearn.neural_network import MLPRegressor
        self.model = MLPRegressor(hidden_layer_sizes=hidden_layers, alpha=alpha,
                                  max_iter=max_iter, random_state=seed)

    def fit(self, rx: np.ndarray, tx: np.ndarray) -> "NeuralEqualizer":
        self.model.fit(_feat(rx), _targ(tx))
        return self

    def predict(self, rx: np.ndarray) -> np.ndarray:
        return _cplx(self.model.predict(_feat(rx)))


def evm(estimate: np.ndarray, reference: np.ndarray) -> float:
    """Error-vector magnitude (rms), normalised to reference power."""
    return float(np.sqrt(np.mean(np.abs(estimate - reference) ** 2)
                         / np.mean(np.abs(reference) ** 2)))


def symbol_ber(estimate: np.ndarray, bits_true: np.ndarray, fmt: str) -> float:
    """BER after demapping equalized symbols to the ``fmt`` constellation."""
    from iq4comm.modulation import get_constellation, demodulate
    const = get_constellation(fmt)
    bits_est = demodulate(estimate, const)
    n = min(len(bits_est), len(bits_true))
    return float(np.mean(bits_est[:n] != bits_true[:n]))
