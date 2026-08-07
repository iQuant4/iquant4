<!-- iQuant4 README -->

# iQuant4

**One engine for optical *and* quantum communications — and their coexistence on a single fiber.**

[![Python](https://img.shields.io/badge/python-3.10%E2%80%933.14-blue)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-Apache--2.0-green)](LICENSE)
[![Validation](https://img.shields.io/badge/evidence-27%20classified%20checks-brightgreen)](VALIDATION.md)
[![Status](https://img.shields.io/badge/status-developer%20alpha%200.2.0a2-orange)](CHANGELOG.md)

**[iquant4.com](https://iquant4.com)** · [GitHub](https://github.com/iQuant4/iquant4)

iQuant4 is a developer-alpha research and design toolkit for fiber-optic links. You
describe a fiber span once, and the same physical model gives you **classical
capacity** (BER, OSNR, reach, 400G coherent design) *and* **quantum key
distribution** estimates (DV/CV-QKD and explicitly labelled scaling proxies) and
the **coexistence** of the two
when a quantum channel shares the fiber with live DWDM traffic.

That coexistence engine is the platform's distinguishing capability: it models
the spontaneous-Raman noise the classical channels inject into the quantum
channel, calibrated to published measurements, and returns the operating point
where both can run on one fiber. Try it live in the browser — no install — via
the **[Coexistence Explorer](explorer/iquant4_explorer.html)**.

---

## Why it matters

Adding quantum-secure key exchange to an existing network usually means "lay a
dedicated dark fiber." iQuant4 lets you ask the real question instead — *can the
quantum channel ride the fiber you already have, and what does it cost the
traffic?* — and get a concrete answer: a launch power, a protocol, a reach, and a
key rate. See the worked
**[400G metro case study](docs/case_study_metro_qkd.md)**: 17 Tb/s of classical
traffic and a positive modeled QKD rate on one 60 km fiber under the stated
receiver, calibration, asymptotic-security, and single-span assumptions.

## Install

```bash
python -m venv .venv
# Windows:  .\.venv\Scripts\activate      macOS/Linux:  source .venv/bin/activate
pip install -e ".[dev,tomography]"   # core, tests, and CV-QKD SDP tools
```

Requires Python 3.10+ and NumPy / SciPy / Matplotlib (installed automatically).

## Quick start — a coexistence link in 10 lines

```python
from iq4comm.qkd import system_operating_point
from iq4comm.dsp import PulseShape, get_fec_code

# One call: every design knob -> both outputs (classical capacity + QKD key rate).
op = system_operating_point(
    distance_km=60, n_channels=40, launch_dbm_per_channel=-21,
    fmt="16QAM", pulse=PulseShape("rrc", 0.2),
    fec=get_fec_code("SD-FEC-20%"), qkd_protocol="dv")

print(f"classical link closes : {op.classical_closes}")
print(f"net classical capacity: {op.capacity_tbps:.1f} Tb/s")
print(f"QKD secret-key rate   : {op.secret_key_rate:.2e} bits/pulse")
```

```text
classical link closes : True
net classical capacity: 4.3 Tb/s
QKD secret-key rate   : 2.82e-03 bits/pulse
```

A full guided walkthrough is in **[docs/getting_started.md](docs/getting_started.md)**.

## What's inside

**`iqcore` — the shared physical-layer engine.** One `FiberSpec` drives both
branches.

- Split-step-Fourier **NLSE propagation** (attenuation, dispersion β₂/β₃, Kerr) with standard fibers (SMF-28 / DSF / LEAF / DCF).
- **EDFA amplifiers** (gain, noise figure, ASE), multi-span link builder, OSNR.
- **WDM grids** (DWDM G.694.1 / CWDM G.694.2) and **WSS/ROADM** routing (super-Gaussian passbands, cascade filter-narrowing, add/drop).
- **Polarization / PMD / PDL** (Jones emulator, Maxwellian DGD, JME measurement).
- Quantum-optics kernel: states, operators, homodyne/Wigner, tomography.

**`iq4comm.dsp` — classical transmission & DSP.**

- **Modulation** (OOK/BPSK/QPSK/16-/64-QAM) with closed-form + Monte-Carlo **BER**.
- **GN nonlinear-interference model** (effective SNR, optimal launch, nonlinear Shannon limit).
- **Pulse shaping** (RRC/RC/sinc/rect/Gaussian) and **FEC** (Reed-Solomon decoding, net coding gain, code catalog).
- **Signal quality**: eye diagram + **Q-factor**, constellation + **EVM/MER**.
- **Coherent recovery**: carrier phase (Viterbi–Viterbi, blind-phase-search), frequency offset, timing (Gardner, Oerder–Meyr). ML equalizers (Volterra + neural).

**`iq4comm.qkd` — quantum communications & coexistence.**

- **DV-QKD** (decoy-state BB84) and **CV-QKD** (GG02 homodyne), plus a generic finite-size **sensitivity estimate** and the **PLOB** bound.
- **Exploratory scaling proxies**: MDI-QKD, Twin-Field QKD, trusted-node relay, and entanglement/repeater models. These are excluded from automatic recommendations.
- **Coexistence engine**: co/counter-propagating Raman background/excess noise with unequal pump/quantum loss and a traceable reproduction of Ferreira da Silva et al. JLT 2014.
- **Whole-system model** + optimizer: every knob (distance, loading, launch, format, roll-off, FEC, ROADM count) → both outputs. Automatic protocol selection is restricted to recommendation-eligible DV/CV research models.

## Validated, not asserted

Every model is benchmarked against a closed-form limit or a published value.
Run the suite:

```bash
python -m validation.validate      # 27 classified automated checks
```

Highlights: fiber loss / BER / Q-factor / PLOB / PMD statistics match their
analytical references; RS(255,239) net coding gain is 6.06 dB versus a 6.2 dB
reference; and locked tests reproduce all 12 digitized co/counter-propagating
Raman points from Ferreira da Silva et al. within 10%. The evidence ledger keeps
analytical checks, literature reproductions, broad reference bands, software
regressions, and proxy sanity checks separate. **No independent hardware
validation is claimed.** See **[VALIDATION.md](VALIDATION.md)**.

## Command line & diagnostics

```bash
iq4comm --version
iq4comm doctor              # environment + reference-physics self-check (add --json)
```

## Showcase & offline docs

Generate the flagship showcase — figures, data, and a self-contained HTML
dashboard — with one command:

```bash
iq4comm showcase all --output-dir showcase_output   # then open showcase_output/index.html
```

Guides: [docs/tutorials/alpha_showcase.md](docs/tutorials/alpha_showcase.md) and
[docs/tutorials/showcase_dashboard.md](docs/tutorials/showcase_dashboard.md).

## Status & scope

**Developer Alpha** (`0.2.0a2`) — the physics APIs are stabilising but may still
change. Models are reduced, asymptotic, or first-order in several places. The
Raman coefficient is receiver-effective and fitted to one published experiment;
it must be recalibrated for another receiver. This toolkit is not a network
design authority, device digital twin, protocol-specific composable-security
proof, or substitute for hardware qualification.

## Learn more

- **[docs/getting_started.md](docs/getting_started.md)** — coexistence design walkthrough.
- **[docs/case_study_metro_qkd.md](docs/case_study_metro_qkd.md)** — the flagship 400G + QKD case study.
- **[VALIDATION.md](VALIDATION.md)** — how we know the numbers are right.
- **[ROADMAP.md](ROADMAP.md)** — what's built and what's next.
- **[CONTRIBUTING.md](CONTRIBUTING.md)** · **[SECURITY.md](SECURITY.md)** · **[CHANGELOG.md](CHANGELOG.md)**

## Repository layout

```text
iquant4/
├── iqcore/       shared physical-layer + quantum-optics engine
├── iq4comm/      classical DSP (dsp/) and quantum comms (qkd/)
├── examples/     runnable demonstrations (incl. the case study)
├── explorer/     the in-browser Coexistence Explorer
├── validation/   the reproducible benchmark suite
├── tests/        analytical / conserved-quantity regression tests
└── docs/         guides, architecture, and release notes
```

## License

Apache-2.0 — see **[LICENSE](LICENSE)**. © Amir Yazdanpour / iQuant4.
