"""Forward error correction: the coding gain that closes real optical links.

Every capacity figure in this platform quietly assumed a pre-FEC BER threshold
(the ``3.8e-3`` "7% hard-decision FEC" number).  This module makes that number
*earned* rather than magic: it models the codes themselves, so the threshold BER,
the net coding gain, and the throughput cost of the overhead all come from the
code parameters instead of a constant.

Two regimes are covered:

* **Hard-decision block codes (Reed-Solomon).**  A bounded-distance RS(n, k)
  decoder over GF(2^m) corrects up to ``t = (n-k)/2`` symbol errors per codeword,
  so the post-decode BER is an exact function of the channel symbol-error
  probability.  From that we compute the *threshold BER* (the pre-FEC BER at
  which the post-FEC BER meets a target such as 1e-15) with no fitting.
* **Soft-decision codes (LDPC / staircase).**  These have no closed-form
  post-decode BER, so they are represented by their published threshold and net
  coding gain, clearly labelled as reference values.

The key figures of merit are the **code rate** ``R = k/n`` (and its overhead),
the **threshold BER**, and the **net coding gain** -- the Eb/N0 saved at a target
output BER *after* paying the rate penalty ``10*log10(1/R)``.  ``coded_net_bitrate``
then ties FEC back to capacity: the line carries ``R`` times as much information
as raw bits, and a format now "closes" whenever its channel BER is under the
code's threshold -- generally a much weaker requirement than an uncoded target,
which is exactly the reach (and, in coexistence, the launch-power) that FEC buys.

References: ITU-T G.975.1 (super-FEC), OIF 400ZR (oFEC), IEEE 802.3 Clause 91
(KP4 RS(544,514)).  RS post-decoding: Lin & Costello, *Error Control Coding*.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import comb, log10

import numpy as np
from scipy.optimize import brentq

from .ber import ber_theory

__all__ = [
    "code_rate",
    "overhead_percent",
    "rs_symbol_error_prob",
    "rs_post_decode_ber",
    "rs_threshold_ber",
    "required_ebn0_db",
    "FECCode",
    "net_coding_gain_db",
    "coded_net_bitrate_bps",
    "FEC_CODES",
    "get_fec_code",
]

TARGET_OUT_BER = 1e-15          # standard post-FEC reference output BER


def code_rate(n: int, k: int) -> float:
    """Code rate ``R = k / n`` (information bits per coded bit)."""
    if not 0 < k < n:
        raise ValueError("require 0 < k < n")
    return k / n


def overhead_percent(n: int, k: int) -> float:
    """FEC overhead ``(n - k) / k`` as a percentage."""
    if not 0 < k < n:
        raise ValueError("require 0 < k < n")
    return 100.0 * (n - k) / k


def rs_symbol_error_prob(ber_in: float, bits_per_symbol: int = 8) -> float:
    """Channel symbol-error probability from the pre-FEC bit-error rate.

    A symbol (``m`` bits) is wrong unless every bit is right:
    ``p_s = 1 - (1 - BER)^m``.  (Independent-bit approximation, standard for RS
    over an interleaved channel.)
    """
    if not 0.0 <= ber_in <= 1.0:
        raise ValueError("ber_in must be in [0, 1]")
    return 1.0 - (1.0 - ber_in) ** bits_per_symbol


def rs_post_decode_ber(ber_in: float, n: int, k: int,
                       bits_per_symbol: int = 8) -> float:
    """Post-decode BER of a bounded-distance RS(n, k) decoder.

    Corrects ``t = (n - k) // 2`` symbol errors.  The residual codeword symbol
    error rate is

        P_s,out ~= (1/n) * sum_{i=t+1}^{n} i * C(n,i) * p_s^i * (1-p_s)^(n-i),

    and the output BER approximates ``P_s,out`` (a symbol error corrupts about
    half its bits, but for RS the conventional bound uses the symbol rate as the
    BER proxy; this is the standard, slightly conservative estimate).
    """
    if n <= k:
        raise ValueError("require n > k")
    t = (n - k) // 2
    p_s = rs_symbol_error_prob(ber_in, bits_per_symbol)
    if p_s <= 0.0:
        return 0.0
    # Sum the tail beyond the correction capability; work in log-safe terms.
    acc = 0.0
    for i in range(t + 1, n + 1):
        acc += i * comb(n, i) * p_s ** i * (1.0 - p_s) ** (n - i)
    return acc / n


def rs_threshold_ber(n: int, k: int, *, target_out_ber: float = TARGET_OUT_BER,
                     bits_per_symbol: int = 8) -> float:
    """Pre-FEC BER at which RS(n, k) reaches ``target_out_ber`` after decoding.

    Solved numerically from :func:`rs_post_decode_ber`.  Channel BERs below this
    threshold are corrected to at least the target; above it the code fails.
    """
    def f(log_ber):
        return rs_post_decode_ber(10.0 ** log_ber, n, k, bits_per_symbol) - target_out_ber

    lo, hi = -9.0, -0.5                       # search 1e-9 .. ~0.3 pre-FEC BER
    if f(lo) > 0:                              # target unreachable even at tiny BER
        return 0.0
    if f(hi) < 0:                              # code corrects even a very bad channel
        return 10.0 ** hi
    return 10.0 ** brentq(f, lo, hi, xtol=1e-4)


def required_ebn0_db(fmt: str, target_ber: float, *,
                     bounds_db: tuple[float, float] = (-2.0, 40.0)) -> float:
    """Eb/N0 (dB) an uncoded ``fmt`` needs to reach ``target_ber`` (AWGN)."""
    def f(ebn0):
        return ber_theory(fmt, ebn0) - target_ber

    lo, hi = bounds_db
    if f(lo) < 0:                              # already below target at min Eb/N0
        return lo
    if f(hi) > 0:                              # cannot reach target in range
        return float("inf")
    return float(brentq(f, lo, hi, xtol=1e-4))


@dataclass(frozen=True)
class FECCode:
    """A forward-error-correction code and its coding-gain characteristics."""

    name: str
    n: int
    k: int
    kind: str = "RS"                          # 'RS' (computed) or 'SD' (reference)
    bits_per_symbol: int = 8                  # RS symbol size (GF(2^m))
    threshold_ber_ref: float | None = None    # for SD codes with no closed form
    ncg_db_ref: float | None = None           # published net coding gain
    reference: str = ""

    @property
    def rate(self) -> float:
        return code_rate(self.n, self.k)

    @property
    def overhead_percent(self) -> float:
        return overhead_percent(self.n, self.k)

    def threshold_ber(self, *, target_out_ber: float = TARGET_OUT_BER) -> float:
        """Pre-FEC BER threshold: computed for RS, reference value for SD."""
        if self.kind.upper() == "RS":
            return rs_threshold_ber(self.n, self.k, target_out_ber=target_out_ber,
                                    bits_per_symbol=self.bits_per_symbol)
        if self.threshold_ber_ref is None:
            raise ValueError(f"{self.name}: no threshold available")
        return self.threshold_ber_ref

    def post_decode_ber(self, ber_in: float) -> float:
        """Post-FEC BER for a channel BER (RS only; SD raises)."""
        if self.kind.upper() != "RS":
            raise ValueError(f"{self.name}: post-decode BER only modelled for RS")
        return rs_post_decode_ber(ber_in, self.n, self.k, self.bits_per_symbol)


def net_coding_gain_db(fmt: str, code: FECCode, *,
                       target_out_ber: float = TARGET_OUT_BER) -> float:
    """Net coding gain (dB): Eb/N0 saved at ``target_out_ber``, rate penalty paid.

    NCG = (Eb/N0)_uncoded@target  -  [ (Eb/N0)_coded-bit@threshold + 10log10(1/R) ].

    The bracketed term is the *information*-bit Eb/N0 the coded system needs: it
    runs at the (much higher) channel BER threshold, but spends ``1/R`` coded
    bits per info bit, so the rate penalty is added back.  A published NCG is used
    directly for soft-decision codes.
    """
    if code.ncg_db_ref is not None and code.kind.upper() != "RS":
        return code.ncg_db_ref
    ebn0_unc = required_ebn0_db(fmt, target_out_ber)
    ebn0_chan = required_ebn0_db(fmt, code.threshold_ber(target_out_ber=target_out_ber))
    rate_penalty = 10.0 * log10(1.0 / code.rate)
    return ebn0_unc - (ebn0_chan + rate_penalty)


def coded_net_bitrate_bps(raw_line_rate_bps: float, code: FECCode, channel_ber: float,
                          *, target_out_ber: float = TARGET_OUT_BER) -> float:
    """Net information rate delivered if the code closes the link, else 0.

    The line carries ``rate * raw`` information bits; the link "closes" only if
    the channel BER is at or below the code's threshold (so the post-FEC BER
    meets the target).  This replaces the hard-coded FEC threshold with a per-code
    decision and charges the overhead honestly.
    """
    if channel_ber <= code.threshold_ber(target_out_ber=target_out_ber):
        return raw_line_rate_bps * code.rate
    return 0.0


# --- Catalog of standard optical FEC schemes -------------------------------
# RS codes are fully computed; SD entries carry published reference values.
FEC_CODES: dict[str, FECCode] = {
    "RS(255,239)": FECCode(
        "RS(255,239)", 255, 239, kind="RS", bits_per_symbol=8,
        reference="ITU-T G.709 first-generation HD-FEC (~6.7% overhead)"),
    "KP4": FECCode(
        "KP4 RS(544,514)", 544, 514, kind="RS", bits_per_symbol=10,
        reference="IEEE 802.3 Clause 91, 400G Ethernet (~5.8% overhead)"),
    "HD-FEC-7%": FECCode(
        "HD-FEC 7% (staircase)", 100, 93, kind="SD",
        threshold_ber_ref=3.8e-3, ncg_db_ref=9.2,
        reference="ITU-T G.975.1 super-FEC / staircase, ~7% overhead"),
    "SD-FEC-20%": FECCode(
        "SD-FEC 20% (LDPC)", 120, 100, kind="SD",
        threshold_ber_ref=2.0e-2, ncg_db_ref=11.3,
        reference="OIF 400ZR-class soft-decision LDPC, ~20% overhead"),
}


def get_fec_code(name: str) -> FECCode:
    """Look up a catalog FEC code by key (see :data:`FEC_CODES`)."""
    try:
        return FEC_CODES[name]
    except KeyError:
        raise ValueError(f"unknown FEC code {name!r}; choose from {list(FEC_CODES)}")
