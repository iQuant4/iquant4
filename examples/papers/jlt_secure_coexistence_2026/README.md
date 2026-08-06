# JLT — Wavelength-Resolved Security-Constrained Launch-Power Optimization

Reproduces every figure, table, and headline number in the manuscript from the
frozen reference configuration in `config.py`.

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
| Fig. (optimization) | `generate_figures.fig_optimization` | DV dies −13.2, CV −21.5, O-band survives to P_GN |
| Fig. (regime map) | `generate_figures.fig_regime` | classical/security transition ~43 km |
| Fig. (load) | `generate_figures.fig_load` | back-off 7.6→16.7 dB (N_c 4→40) |
| Fig. (multi-span) | `generate_figures.fig_multispan` | O-band QKD dies past 1 span |
| Fig. (R_min) | `generate_figures.fig_rmin` | P* flat over 10–10⁴ bit/s |
| Headline (Table III) | `run_all.headline` | P_GN −2.93; DV −13.2/27%; CV −21.5/54% |
| Table IV (Fock chi_BE) | `fock_chi_be.py` | Fock vs symplectic ≤ 0.1% at N=20 |
| Table (Fock primitives) | `fock_validation.py` | rel err ≤ 1e-12 |
| GN-vs-SSFM | `ssfm_gn.py` | NLI ∝ P^~2.9; η within 3 dB |

## Reproducibility

- `config.py` is the single source of truth; changing it changes all outputs.
- `fock_chi_be.py`, `fock_validation.py`, `raman_dv_cv_audit.py` require only
  numpy + scipy. The figure scripts and `ssfm_gn.py` require the iQuant4 platform
  (`pip install -e .` at the repo root).
- Pin the platform version to the tagged release cited in the manuscript.
