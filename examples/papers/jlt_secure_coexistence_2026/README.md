# JLT — Wavelength-Resolved Security-Constrained Launch-Power Optimization

Regenerates every figure, table, and headline number from the frozen reference
configuration in `config.py`. The outputs below supersede manuscript drafts
that used the earlier effective-length Raman approximation.

## One command

```bash
python run_all.py            # headline numbers + all figures
```

Then the three validations (each self-contained beyond the platform):

```bash
python fock_chi_be.py        # Table IV: first-principles Fock chi_N(B:E) vs symplectic
python fock_validation.py    # Table III: Fock entropy-primitive convergence
python raman_dv_cv_audit.py  # DV/CV common Raman normalization audit
```

## What maps to what

| Manuscript object | Script / function | Expected result |
|---|---|---|
| Fig. (Raman profile) | `generate_figures.fig_raman_profile` | silica peak ~13 THz; O-band 32 dB down |
| Fig. (optimization) | `generate_figures.fig_optimization` | corrected Raman curves and the classical GN optimum |
| Fig. (regime map) | `generate_figures.fig_regime` | security ceiling compared with the GN optimum |
| Fig. (load) | `generate_figures.fig_load` | security ceiling versus channel loading |
| Fig. (multi-span) | `generate_figures.fig_multispan` | O-band QKD dies past 1 span |
| Fig. (R_min) | `generate_figures.fig_rmin` | P* flat over 10–10⁴ bit/s |
| Headline (Table III) | `run_all.headline` | P_GN −2.93 dBm/ch; DV and CV constraints do not bind at this configuration |
| Table IV (Fock chi_BE) | `fock_chi_be.py` | Fock vs symplectic ≤ 0.1% at N=20 |
| Table (Fock primitives) | `fock_validation.py` | rel err ≤ 1e-12 |
| GN-vs-SSFM | `ssfm_gn.py` | NLI ∝ P^~2.9; η within 3 dB |

## Reproducibility

- `config.py` is the single source of truth; changing it changes all outputs.
- `P_sec,max` is the largest launch power meeting the modeled security floor;
  the actual operating point is `P* = min(P_GN, P_sec,max)`. This distinction
  prevents a non-binding security ceiling above `P_GN` from being reported as
  a negative back-off.
- `fock_chi_be.py`, `fock_validation.py`, `raman_dv_cv_audit.py` require only
  numpy + scipy. The figure scripts and `ssfm_gn.py` require the iQuant4 platform
  (`pip install -e .` at the repo root).
- Pin the platform version to the tagged release cited in the manuscript.
