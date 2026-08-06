# iQuant4 — Launch Checklist

*An honest map of what's done, what's days away, and what's months out — so you
can pick a launch definition deliberately instead of by feel.*

---

## Where you are tonight

In one intense build cycle the platform went from a repo that wouldn't push to a
validated, end-to-end optical **and** quantum communication simulator with a
scan-confirmed differentiator. Concretely, on `github.com/iQuant4/iquant4`:

**Physical layer (`iqcore.fiber`)** — split-step NLSE propagation, standard
fibers (SMF-28/DSF/LEAF/DCF), EDFA amplifiers, multi-span links + OSNR, WDM
grids (DWDM G.694.1 / CWDM G.694.2), and digital backpropagation.

**Classical comms (`iq4comm.dsp`, `iq4comm.ml`)** — OOK/BPSK/QPSK/16-/64-QAM,
coherent BER (theory + Monte-Carlo), the Gaussian-Noise nonlinear model with
optimal-launch/reach, and a learned-equalizer ML layer.

**Quantum comms (`iq4comm.qkd`)** — DV decoy-state BB84, CV GG02 homodyne, the
PLOB bound, **classical–quantum DWDM coexistence** (Raman-calibrated to
da Silva et al. JLT 2014), and a **joint coexistence optimizer**.

**Engineering** — full test suite (analytical/literature-validated, ~90 cases),
CI across 5 OS/Python combos, packaging, CLI, docs/portal tooling, Apache-2.0.

**The differentiator** — one `FiberSpec` drives classical capacity, DV/CV-QKD,
their coexistence coupling, *and* the optimizer that solves for the operating
point. Your literature/tool scan found no released tool that unifies these.

Honest headline: **~80% to a credible open-source launch; ~30–40% to a product a
customer pays for.** The science is the hard part and it's largely done; the
remaining distance is a different kind of work (packaging, then credibility).

---

## Do first — quick cleanup (hours)

These are loose ends from the build; clear them before any launch.

- [ ] **Retire the duplicate repo** `iQuant4/iquant4comm-core` (archive on
      GitHub) so there is one canonical repo.
- [ ] **Commit or `.gitignore`** the stray `iQuant4_HOSTED_VERIFY_15A.ps1` and
      any `logs/` transcripts so `git status` is clean.
- [ ] **Confirm the CI run is green** on GitHub Actions after today's pushes
      (the scikit-learn dependency fix should make the ML tests pass).
- [ ] Delete the mis-named `tests/test_coexistence_cv.py` duplicate if it's
      still there (keep `tests/test_cv_coexistence.py`).

---

## Launch A — Open-source technical release  ·  ~80% done  ·  ~1–2 weeks

*Definition: anyone can `pip install`, read docs, and cite it; a tagged release
exists and it's been announced.* This is the realistic near-term launch.

**Done**
- [x] Public repo, Apache-2.0 license, README (now reflects the full platform)
- [x] Validated test suite + CI (5 OS/Python combos)
- [x] Packaging (`pyproject.toml`, wheel/sdist build in CI)
- [x] Capstone end-to-end showcase (`examples/iquant4_showcase.py`)

**Remaining**
- [ ] **Publish to PyPI** — register the name, `python -m build`, `twine upload`;
      test `pip install iq4comm` in a clean venv. *(½–1 day)*
- [ ] **Deploy the docs site** — you already have a portal builder + a Pages
      workflow; wire it to GitHub Pages so docs are live at a URL. *(½–1 day)*
- [ ] **Tag `v0.1.0`** with GitHub release notes summarizing the platform.
      *(hours)*
- [ ] **README badge row** — CI status, PyPI version, license, docs link.
      *(hours)*
- [ ] **A "start here" notebook** — the capstone as a runnable, narrated
      notebook (fiber → link → BER → QKD → coexistence). *(1 day)*
- [ ] **Announcement** — a short blog/LinkedIn post + posts to relevant
      communities (photonics/optics, QKD, r/Physics, HN if it lands). Lead with
      the coexistence differentiator and the figures. *(1–2 days)*
- [ ] *(High-leverage optional)* **A short arXiv note** on the unified
      coexistence engine + optimizer. This is what turns "cool repo" into
      "citable contribution" and is the single best credibility multiplier for a
      solo deep-tech founder. *(1–2 weeks writing)*

---

## Launch B — Hosted / usable product  ·  ~30–40%  ·  ~2–3 months

*Definition: a non-coder can use it — input a route + channel plan in a browser,
get the operating point back.* This is where "library" becomes "platform."

- [ ] **Web UI or API** wrapping `optimize_launch_power` / `coexistence_curve`:
      enter fiber, distance, channel count, QKD target → return the operating
      point + Pareto plot. *(the core product surface; weeks)*
- [ ] **Interactive explorer** (your "Experiences" pillar) — sweep launch power
      and distance, watch capacity/key-rate/constellation update live. A great
      demo and investor artifact. *(weeks)*
- [ ] **Hosting/deploy** — a small cloud service; auth if multi-user. *(days–weeks)*
- [ ] **Differentiable optimizer (the moat)** — port the fiber→QKD chain to
      JAX/PyTorch for gradient-based joint optimization over many variables
      (per-channel powers, wavelength plan, DBP filters). *Blocked until you set
      up the JAX/PyTorch toolchain in your environment.* *(a real project)*

---

## Launch C — Customer- / investor-credible  ·  different axis  ·  months, mostly non-code

*Definition: someone bets money or a network on your numbers.* The gap here is
**not code** — it's trust.

- [ ] **Real validation** — reproduce one measured result from a coexistence
      experiment end-to-end, or (stronger) validate against data from a fiber
      testbed you or a partner runs. Today everything is validated against
      textbook formulas + one literature calibration point — enough for a tool,
      not yet for a procurement decision.
- [ ] **A design partner** — a QKD lab, a telecom operator, or a university group
      who uses it and vouches. This is the highest-value and longest-lead item.
- [ ] **The paper** (peer-reviewed or arXiv) — the credible anchor.
- [ ] **Pitch narrative** — the problem (QKD-over-DWDM planning is unowned), the
      wedge (unified, calibrated, optimizable), the evidence (your figures), the
      ask.

---

## Honest caveats to state publicly (protect credibility)

Being upfront about these *raises* trust, and your README already sets the right
tone. Keep stating:

- **Asymptotic key rates**, not composable finite-key security.
- **Reduced/analytical models** in places (GN model, per-symbol Kerr channel for
  the ML demo, single-span coexistence).
- **One calibration point** for the Raman coefficient (da Silva 2014, factor-of-a-
  few uncertainty) — a knob to recalibrate to real hardware.
- **No experimental/hardware validation yet.** It's a modeling platform.

---

## What only you can do (the non-code path)

The engineering is largely a solved problem now; the company isn't built in a
repo. The three things that move iQuant4 from "impressive simulator" to
"venture" are: (1) a **design partner / first user**, (2) a **paper** that makes
the differentiator citable, and (3) a **narrative** that positions the unowned
QKD-DWDM-coexistence seam as the wedge. None of those are code — and they're the
real launch.

---

## Recommended path

1. **This week:** cleanup + Launch A mechanics (PyPI, docs deploy, tag, badges,
   notebook). You're days from a legitimate open-source release.
2. **Next:** write the arXiv note — it serves Launch A (credibility) *and* Launch
   C (citable anchor) at once.
3. **In parallel, non-code:** start one design-partner conversation. That clock
   is the longest, so start it early.
4. **When you have the toolchain:** the hosted UI + differentiable optimizer for
   Launch B.

*Pick Launch A as the concrete near-term target — it's real, it's close, and it
creates the artifacts every later launch builds on.*
