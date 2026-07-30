# iQuant4 developer-alpha showcase

The showcase turns the current scientific capabilities into three reproducible
workflows with machine-readable results and publication-ready PNG figures.
It is intended for demonstrations, installation checks, reviewer previews, and
release validation.

## Run the complete showcase

From an editable source installation:

```powershell
iq4comm showcase all --output-dir showcase_output
```

Or through the module entry point:

```powershell
python -m iq4comm showcase all --output-dir showcase_output
```

The command creates:

```text
showcase_output/
├── index.html
├── iQuant4_showcase_standalone.html
├── dashboard_data.json
├── showcase_manifest.json
├── receiver_family/
│   ├── receiver_family_report.txt
│   ├── receiver_family_results.csv
│   ├── receiver_family_results.json
│   └── receiver_family_ber.png
├── lossy_cat/
│   ├── lossy_cat_metrics.csv
│   ├── lossy_cat_metrics.json
│   └── lossy_cat_wigner.png
└── sign_free_tomography/
    ├── tomography_summary.json
    └── tomography_reconstruction.png
```

Open the generated dashboard with:

```powershell
Start-Process .\showcase_output\index.html
```

Use `--open` to launch it automatically, or rebuild it later without rerunning
any simulation:

```powershell
iq4comm showcase dashboard --output-dir showcase_output
```

The tomography figure is produced when the optional CVXPY dependency is
installed. Without CVXPY, the showcase records a transparent `skipped` result
in `tomography_summary.json`. To require tomography and fail when the solver is
missing, use:

```powershell
iq4comm showcase tomography --require-cvxpy
```

## 1. Receiver-family optimization

```powershell
iq4comm showcase receiver-family --output-dir showcase_output
```

This workflow solves a communication design problem: it optimizes erasure PNR,
homodyne, and heterodyne receivers under the same minimum-acceptance constraint
and reports the best family as fiber distance changes.

The CSV and JSON artifacts include optimized thresholds, acceptance
probabilities, conditional BER, and the winner at each distance.

## 2. Loss-degraded cat state

```powershell
iq4comm showcase lossy-cat --output-dir showcase_output
```

This workflow applies a bosonic pure-loss channel to an even cat state and
tracks:

- mean photon number;
- state purity;
- Wigner normalization;
- integrated Wigner negativity.

The Wigner panels show how attenuation suppresses nonclassical interference
fringes and pulls the state toward vacuum.

## 3. Sign-free tomography

```powershell
iq4comm showcase tomography --output-dir showcase_output --require-cvxpy
```

The quick tomography profile reconstructs a single-photon Fock state from
sign-free quadrature histograms. It validates the vectorized measurement map,
solves the positive-semidefinite reconstruction problem, and reports fidelity,
probability RMSE, trace, and the minimum eigenvalue.

This quick profile is designed for the developer alpha. The existing cat and
paper-scale GKP examples remain available under `examples/tomography/` for
heavier scientific validation.

## Python API

```python
from pathlib import Path
from iq4comm.showcase import run_alpha_showcase

manifest = run_alpha_showcase(Path("showcase_output"))
print(manifest["manifest_path"])
```

Each individual workflow also has its own API:

```python
from iq4comm.showcase import (
    run_lossy_cat_showcase,
    run_receiver_family_showcase,
    run_sign_free_tomography_showcase,
)
```

## Scope and interpretation

These examples validate numerical models under their documented assumptions.
They do not by themselves establish hardware fidelity, finite-key security, or
composable QKD security. See `docs/architecture/conventions.md` and
`docs/release/validation.md` for the current scientific conventions and
limitations.
