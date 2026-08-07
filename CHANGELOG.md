# Changelog

## 0.2.0a2 — Scientific and release hardening

This release corrects the coexistence distance law, narrows engineering claims,
and synchronizes the Python package, browser explorer, evidence, documentation,
and distributions around one model contract.

### Corrected

- Replaced the nonlinear-effective-length Raman approximation with the physical
  co-propagating and counter-propagating longitudinal integrals, including
  unequal pump/quantum attenuation and numerically stable equal-loss limits.
- Corrected multi-span Raman accumulation and mixed-band pump/quantum loss.
- Replaced a mistaken reading of the `x10^-4` axis in Ferreira da Silva et al.
  Fig. 4 with a traceable 12-point digitized dataset and frozen reproduction
  tests. The default coefficient is now explicitly receiver-effective.

### Guardrails

- Classified TF-QKD, MDI-QKD, trusted-node, and repeater calculations as
  `scaling_proxy`; classified the generic finite-size correction as
  `sensitivity_estimate`.
- Excluded scaling proxies from automatic protocol selection and required an
  explicit opt-in in high-level workflows.
- Added an evidence ledger that distinguishes analytical verification,
  literature reproduction, reference-band checks, software regressions, and
  proxy sanity checks. No independent hardware validation is claimed.

### Synchronized

- Added a browser/Python physics contract with parity tests for Raman, GN SNR,
  WSS narrowing, ROADM loss, QKD rates, and complete operating points.
- Regenerated the metro case study, validation narrative, website explorer,
  wheel, and source distribution from the hardened source tree.

## 0.2.0a1 — Coexistence platform

This release turns the alpha into a full optical-and-quantum coexistence engine:
the classical and quantum branches now share one physical model end to end, every
model is benchmarked, and the platform ships an interactive explorer and a worked
case study.

### Added — classical physical layer & DSP

- **WSS / ROADM routing** (`iqcore.fiber.wss`): super-Gaussian passbands, cascade
  filter-narrowing (`B_eff = B_3dB·(1/k)^(1/2·order)`), the roll-off-dependent
  narrowing penalty, and add/drop/express on a `WDMComb`.
- **Polarization / PMD / PDL** (`iqcore.fiber.polarization`): Jones-section PMD
  emulator with Maxwellian DGD statistics, JME DGD measurement, the `D√L` law,
  PDL elements, and a PMD → polarization-QBER tie to QKD.
- **Pulse shaping** (`iq4comm.dsp.pulse_shaping`): RRC/RC/sinc/rect/Gaussian,
  occupied bandwidth, Nyquist spacing, spectral efficiency, residual ISI.
- **Forward error correction** (`iq4comm.dsp.fec`): Reed-Solomon decoding
  waterfall, computed threshold BER, net coding gain, and a catalog of standard
  optical codes (RS(255,239), KP4, 7% HD, 20% SD).
- **Signal-quality metrics**: eye diagram + Q-factor (`iq4comm.dsp.eye`) and
  constellation + EVM/MER (`iq4comm.dsp.constellation`).
- **Coherent recovery** (`iq4comm.dsp.carrier_recovery`): Viterbi–Viterbi and
  blind-phase-search carrier recovery, M-th-power frequency-offset estimation,
  Gardner and Oerder–Meyr timing recovery.

### Added — quantum communications & coexistence

- **Finite-key security** (`iq4comm.qkd.finite_key`) for DV/MDI/TF and CV.
- **Reach-extension protocols** (`iq4comm.qkd.protocols`): MDI-QKD, Twin-Field
  QKD, trusted-node relay.
- **Coexistence engine** (`iq4comm.qkd.coexistence`): spontaneous-Raman
  background (DV) and excess noise (CV), calibrated to da Silva et al. JLT 2014.
- **Wavelength-resolved Raman** (`iq4comm.qkd.raman_spectrum`): silica Raman gain
  profile × Bose–Einstein Stokes/anti-Stokes factor, anchored to the C-band
  calibration and predicting band-dependent coupling (e.g. O-band ≈32 dB quieter).
- **Multi-span coexistence** (`iq4comm.qkd.multispan`): amplified classical spans
  with an un-amplifiable quantum channel (full end-to-end loss + accumulated
  Raman); reduces exactly to the single-span engine at N=1.
- **Coexistence optimizer & protocol selection** (`iq4comm.qkd.optimize`):
  constrained launch-power solve and best-protocol-for-a-route.
- **Format / roll-off / FEC tie-ins** (`iq4comm.qkd.format_impact`,
  `spectral_design`) folding every classical knob into the QKD channel.
- **Whole-system model** (`iq4comm.qkd.system_model`): all knobs → both outputs
  in one call, including the ROADM-loss → QKD coupling.
- **Entanglement distribution & quantum repeaters** (`iq4comm.qkd.repeater`):
  Werner-state swapping and a memory-assisted repeater that beats the PLOB bound.

### Added — packaging, validation, experience

- **Validation suite** (`validation/validate.py`) and **VALIDATION.md**: 21/21
  checks against closed-form limits and published references, with caveats.
- **Interactive Coexistence Explorer** (`explorer/iquant4_explorer.html`): a
  self-contained, in-browser lab whose physics matches the Python engine.
- **Flagship case study** (`examples/case_study_metro_qkd.py`,
  `docs/case_study_metro_qkd.md`): a QKD overlay on a live 400G metro DWDM link.
- Refreshed README, project URLs, and PyPI metadata; version bumped to `0.2.0a1`.

### Changed

- Cross-cutting design levers (format, pulse-shaping roll-off, FEC, ROADM count)
  are backward compatible — a `None`/`0` argument reproduces prior behaviour.

## 0.1.0a1 — Developer alpha in progress

### Added

- Shared `iqcore` state, operator, measurement, optics, phase-space, metrics,
  visualization, channel, and tomography namespaces.
- `iq4comm` coherent sources, fiber channels, receiver families, metrics, and
  receiver optimization.
- Backward-compatible wrappers for the original research modules.
- Scientific regression tests and architecture guards.
- Initial packaging metadata and developer-alpha documentation.
- Reusable receiver-family comparison API for erasure PNR, homodyne, and
  heterodyne receiver optimization.
- `iq4comm-receiver-family` command-line entry point.
- Headless alpha quick start and receiver-family tutorial.
- Unified `iq4comm` command with `doctor` and `receiver-family` subcommands.
- Runtime installation diagnostics with text and JSON reports.
- Isolated wheel-install verification outside the source checkout.
- Windows and Ubuntu continuous-integration workflow across Python 3.10–3.14.
- Python 3.10-compatible TOML parsing in development tests and verification tools.

### Release hardening

- Added selectable Apache-2.0 or MIT licensing with PEP 639 metadata.
- Added contribution, security, citation, public-API, validation, and release
  checklist documentation.
- Added wheel and source-distribution release-gate verification.
- Added issue and pull-request templates and repository-hygiene rules.
- Added generated scientific validation reporting.
- Added the `iq4comm showcase` command and reusable showcase API.
- Added receiver-family CSV/JSON/figure artifacts.
- Added loss-degraded cat-state metrics and Wigner gallery.
- Added an optional quick sign-free tomography showcase.
- Added flagship-showcase documentation and release gates.
- Added a responsive offline showcase dashboard with folder-relative and
  standalone embedded-image HTML outputs.
- Added `iq4comm showcase dashboard` and the `--open` showcase option.
- Added dashboard summaries for receiver optimization, Wigner negativity, and
  sign-free tomography, plus the four-branch iQuant4 roadmap.

### Installed documentation portal

- Added `iq4comm docs build` and `iq4comm docs open`.
- Added a responsive, offline documentation portal generated from installed packages.
- Added searchable public API inventories for `iqcore` and `iq4comm`.
- Added isolated-wheel verification for documentation generation.

### Public-preview portal

- Added `iq4comm portal build/open` for one-folder static publication.
- Added an offline landing page that links installed documentation and showcase artifacts.
- Added a manual GitHub Pages deployment workflow.
- Added the public roadmap, community code of conduct, and preview release guide.

### Repository readiness

- Added repository-hygiene verification for staged and tracked files.
- Added Git workflow, governance, GitHub launch, and branch-protection guidance.
- Added Dependabot configuration for Python and GitHub Actions dependencies.
- Added a manual release-candidate workflow that builds and verifies artifacts
  without publishing them.
- Added stricter ignore rules for virtual environments, migration bundles,
  generated portals, credentials, private keys, and local research data.
