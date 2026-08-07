# iQuant4 Roadmap

`iqcore` is the shared scientific engine. The first product branch,
**iQuant4Comm (`iq4comm`)**, is active in the developer alpha; three more
branches are planned under the iQuant4 umbrella. A detailed component-level
roadmap and build log is maintained alongside this file; this document is the
public summary.

## Active in the developer alpha — iQuant4Comm (`iq4comm`)

The alpha is a unified engine for **optical and quantum communications, and their
coexistence on one fiber**. The implementation has 27 classified evidence checks
plus a broader regression suite; see `VALIDATION.md` for what each class does and
does not establish.

**Physical layer (`iqcore`).** Split-step-Fourier NLSE propagation (attenuation,
dispersion, Kerr); standard fibers (SMF-28/DSF/LEAF/DCF); EDFA amplifiers and
multi-span links with OSNR; WDM grids (DWDM G.694.1 / CWDM G.694.2); WSS/ROADM
wavelength routing with cascade filter-narrowing; polarization / PMD / PDL with
Maxwellian DGD statistics; and the quantum-optics kernel (states, operators,
homodyne/Wigner, tomography).

**Classical DSP (`iq4comm.dsp`).** Modulation (OOK/BPSK/QPSK/16-/64-QAM) with
closed-form and Monte-Carlo BER; the GN nonlinear-interference model; pulse
shaping; Reed-Solomon FEC with net-coding-gain; eye-diagram/Q-factor and
constellation/EVM diagnostics; coherent carrier and timing recovery; and ML
equalizers.

**Quantum communications (`iq4comm.qkd`).** DV decoy-state BB84 and CV GG02
research models; a generic finite-size sensitivity estimate; explicitly labelled
MDI, Twin-Field, trusted-node, and repeater scaling proxies; the PLOB bound; the
co/counter-propagating Raman **coexistence engine** with a 12-point literature
reproduction; a guarded coexistence optimizer/protocol selector; and a
whole-system model mapping design knobs to classical and quantum outputs.

**Experience & validation.** An in-browser Coexistence Explorer, a reproducible
validation suite, and a flagship 400G-metro-plus-QKD case study.

## Planned branches

- **iQuant4Compute (`iq4compute`)** — quantum circuits, simulators, algorithms,
  control, and error correction.
- **iQuant4Sense (`iq4sense`)** — quantum sensing, imaging, estimation,
  interferometry, and metrology.
- **iQuant4Photonics (`iq4photonics`)** — photonic devices, integrated
  components, system models, and inverse design.

AI and optimization are cross-cutting capabilities reused across branches, with
shared numerical interfaces kept in `iqcore` rather than duplicated.

## Dependency rule

Application branches may depend on `iqcore`. `iqcore` must never depend on an
application branch. Shared functionality used by more than one branch should be
moved into `iqcore` rather than duplicated.

## What's next

Near-term, on the communications branch: one serializable route/scenario model;
uncertainty and validity warnings; independent hardware or partner data;
cross-checking GN against a multi-channel SSFM dataset; report export; and public
API hardening. Broad expansion into the other branches begins only after the
coexistence-planning workflow is calibrated, documented, and independently
tested.
