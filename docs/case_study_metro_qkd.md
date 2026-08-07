# Case Study — QKD Overlay on a 400G-Class Metro DWDM Scenario

This developer-alpha case study asks whether a modeled 60 km route can keep a
40-channel coherent service closed while an in-band QKD channel is present. It
is a reproducible scenario analysis, not a customer design or hardware claim.

Run the exact calculation with:

```bash
python -m examples.case_study_metro_qkd
```

## Scenario

| Input | Value |
|---|---:|
| Fiber | 60 km nominal SMF-28, 0.2 dB/km |
| Classical loading | 40 channels |
| Format | dual-polarization 16-QAM |
| Symbol rate / grid | 64 GBd / 75 GHz |
| FEC | 20% SD-FEC, modeled threshold (2\times10^{-2}) |
| Candidate margin | 3 dB above the modeled close threshold |
| QKD reporting clock | 1 GHz, for bits/pulse-to-bits/s illustration only |
| Raman direction | co-propagating |

## 1. Classical close point

The reduced GN/BER/FEC model places the minimum close point at approximately
**−24.2 dBm/channel**. The candidate operating point is therefore
**−21.2 dBm/channel**. At that point:

- modeled pre-FEC BER is approximately (2.4\times10^{-3});
- the link remains below the selected FEC threshold;
- modeled net payload is **426.7 Gbit/s per channel**, or **17.1 Tbit/s** over
  40 dual-polarization channels.

The 17.1 Tbit/s figure is the configured line-rate/FEC arithmetic once the link
closes. It is not a measured field throughput.

## 2. QKD values at the same point

| Model | Status | Bits/pulse | Illustration at 1 GHz |
|---|---|---:|---:|
| DV-BB84 decoy | `research_model` | (2.82\times10^{-3}) | 2.82 Mbit/s |
| CV-QKD homodyne | `research_model` | (1.31\times10^{-2}) | 13.1 Mbit/s |
| Twin-Field | `scaling_proxy` | (7.47\times10^{-3}) | exploratory only |
| MDI-QKD | `scaling_proxy` | (2.73\times10^{-3}) | exploratory only |

Automatic selection evaluates only recommendation-eligible models. In this
scenario it reports CV as the larger of the eligible DV/CV research-model
values. That is a model comparison, not a recommendation to deploy CV-QKD. A
CV system may share coherent-optics concepts or components with classical
receivers, but it is not a drop-in reuse of a classical coherent transponder.

The TF and MDI values require explicit opt-in and cannot win automatic
selection. Their implementations preserve qualitative loss scaling but omit
protocol-specific decoy estimation, stabilization, finite-key proofs, and
hardware constraints.

## 3. Reach sensitivity

With the example thresholds (`1e-6` bits/pulse and `1e12` bit/s classical
capacity), the current asymptotic/reduced models return approximately:

- **DV-BB84: 201 km**;
- **Twin-Field proxy: 319 km** for the case-study 64 GBd / 75 GHz configuration.

These are model-boundary sensitivities, not independently validated deployment
reach. The TF figure is a scaling-proxy output and is not an engineering result.

## Result and decision boundary

For the stated assumptions, the modeled classical link closes and both eligible
DV/CV research models return a positive key rate at the candidate operating
point. That establishes a useful developer-alpha feasibility hypothesis for the
60 km route.

It does **not** establish that an operator can deploy the overlay without a
capacity penalty. Before a real design decision, the route needs:

- measured span, connector, splice, ROADM, and wavelength-dependent loss;
- the actual classical channel plan and launch powers;
- receiver-specific Raman filtering and detector calibration;
- propagation-direction and multispan configuration;
- protocol-specific finite-key/security analysis;
- uncertainty and sensitivity reporting; and
- laboratory or field validation against the intended hardware.

## Raman evidence used

The default effective coefficient is fitted to a locked digitization of
Configuration G in Ferreira da Silva et al., JLT 32 (2014), Figure 4. The source
axis is counts per trigger multiplied by (10^{-4}). All six co-propagating and
six counter-propagating digitized points are stored with provenance in
`validation/golden/raman_da_silva_2014.json` and reproduced within 10% by tests.
The coefficient absorbs the cited experiment's receiver filtering/collection
conventions and must be recalibrated for another receiver.
