# iQuant4 Evidence and Validation Report

iQuant4 `0.2.0a2` reports evidence by class. A passing unit regression, an
analytical identity, a broad literature range, and reproduction of published
experimental data are useful for different reasons and are not combined into
one claim of “scientific validation.”

Run the evidence ledger with:

```bash
python -m validation.validate
```

Current result: **27/27 automated checks are within their explicit tolerance.**
This means the checks pass; it does not mean every model is experimentally
validated.

## Evidence ledger

| Evidence class | Checks | What it establishes |
|---|---:|---|
| Analytical verification | 11 | Agreement with a closed form, conserved quantity, or directly derived mathematical limit |
| Literature reproduction | 1 | A locked published-experiment operating point is reproduced within the declared digitization tolerance |
| Reference band | 11 | A reduced model lands within a published, textbook, standard, or typical range |
| Software regression | 2 | Two implementations or reductions remain internally consistent |
| Scaling-proxy sanity | 2 | A deliberately reduced proxy preserves its intended qualitative scaling |
| Independent hardware validation | **0** | No independent iQuant4 laboratory or field dataset has yet been supplied |

The test suite additionally checks the full 12-point Raman literature series and
browser/Python parity. Those tests are intentionally not counted as 12 more
independent experiments.

## Raman coexistence correction

For launched pump power (P_0), local effective coefficient ρ, receiver
bandwidth (B), span (L), pump loss (α_p), and quantum-path loss (α_q),
the receiver-side Raman power uses the longitudinal path integral.

For co-propagation:

\[
I_{\mathrm{co}}(L)=
\frac{e^{-\alpha_qL}-e^{-\alpha_pL}}{\alpha_p-\alpha_q},
\qquad
I_{\mathrm{co}}(L)\xrightarrow{\alpha_p=\alpha_q}
Le^{-\alpha L}.
\]

For counter-propagation:

\[
I_{\mathrm{counter}}(L)=
\frac{1-e^{-(\alpha_p+\alpha_q)L}}{\alpha_p+\alpha_q}.
\]

The implementation is tested against direct numerical quadrature, equal- and
near-equal-loss limits, unequal C/O-band losses, both directions, and multispan
accumulation. The prior nonlinear effective length,
((1-e^{-\alpha L})/\alpha), is still valid for Kerr nonlinear phase but is not
the co-propagating receiver-side Raman collection law.

## Published Raman reproduction

The absolute default uses a receiver-effective fit to Configuration G in
Ferreira da Silva et al., *J. Lightwave Technology* 32(13), 2332–2339 (2014),
[arXiv:1410.0656](https://arxiv.org/abs/1410.0656).

An earlier project calibration read the Figure 4 vertical axis as raw counts per
gate. The figure is labeled **counts per trigger × (10^{-4})**. Consequently,
the 60 km co-propagating point is approximately (1.2\times10^{-4}), not 0.15.

The corrected evidence package is
`validation/golden/raman_da_silva_2014.json`. It records:

- source, figure/table, extraction method, date, and axis multiplier;
- 14 channels at −10.5 dBm/channel;
- 1546.12 nm quantum wavelength, 10 GHz filter, 2.5 ns gate, and 15% detector efficiency;
- six co-propagating and six counter-propagating digitized points; and
- frozen fit parameters and a 10% per-point acceptance tolerance.

All 12 points pass. The fitted co-propagating coefficient is
(4.7081\times10^{-10}\,(\mathrm{km\,nm})^{-1}) at an effective measured loss of
0.300 dB/km. This coefficient absorbs the source experiment's receiver
filtering/collection convention. It is **not** a universal silica material
constant and must be recalibrated for another receiver.

## Browser/Python contract

The offline explorer loads `explorer/physics_contract.js`. Node-based contract
tests compare it with the canonical Python engine for:

- equal/unequal-loss Raman path integrals and both directions;
- absolute Raman background yield;
- WSS narrowing and ROADM insertion loss;
- GN-model channel SNR;
- DV and explicitly opted-in TF key rates; and
- a complete operating point with format, roll-off, FEC, and ROADMs.

The TF result is labeled `scaling_proxy` in both runtimes and cannot produce an
engineering feasibility verdict.

## Model-status boundary

| Calculation | Status | Automatic recommendation eligible? |
|---|---|---:|
| DV-BB84 decoy coexistence | `research_model` | Yes, within developer-alpha scope |
| CV-QKD coexistence | `research_model` | Yes, within developer-alpha scope |
| MDI-QKD | `scaling_proxy` | No |
| Twin-Field QKD | `scaling_proxy` | No |
| Trusted-node relay | `scaling_proxy` | No |
| Repeater model | `scaling_proxy` | No |
| Generic Hoeffding finite-size correction | `sensitivity_estimate` | Not a protocol-specific composable proof |

High-level MDI/TF workflows require explicit `allow_scaling_proxy=True` opt-in.
Automatic selection considers only eligible DV/CV research models; proxy values
may be reported for comparison but cannot win.

## Other analytical/reference checks

The ledger covers, among other items:

- fiber pure loss, SMF-28 loss and β₂;
- theoretical/Monte-Carlo QPSK BER and Q-factor conversion;
- GN-model optimum against its closed-form (P_{\mathrm{opt}});
- RS and SD-FEC reference behavior;
- PLOB at 100 km and asymptotic decoy-BB84 reach band;
- silica Raman peak and first-order O-band suppression;
- PMD/DGD statistics and phase-noise variance; and
- BBM92/Werner-state analytical consistency.

Reference-band and proxy-sanity rows do not demonstrate predictive accuracy.
Their purpose is to detect gross convention or scaling errors.

## What remains unvalidated

- No independent iQuant4 hardware or field dataset has been supplied.
- The default Raman coefficient is based on one published receiver/configuration.
- The wavelength-resolved Raman spectrum is a first-order extrapolation.
- GN has not been cross-validated here against a full multi-channel SSFM dataset.
- DV/CV results use reduced/asymptotic security models.
- The finite-size calculation is a sensitivity estimate, not a complete
  protocol-specific composable-security proof.
- TF, MDI, trusted-node, and repeater rates are scaling proxies.
- Uncertainty propagation, component inventories, and calibration versioning are
  not yet a complete product workflow.

## Reproduce

```bash
python -m validation.validate
python -m pytest -q
python -m examples.case_study_metro_qkd
```

For the full paper-specific figure set, use the scripts under
`examples/papers/jlt_secure_coexistence_2026/`, treating their outputs as
manuscript research artifacts rather than customer design reports.
