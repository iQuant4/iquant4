# Offline iQuant4 showcase dashboard

The developer alpha can combine its flagship scientific artifacts into a
single offline dashboard. No web server, cloud account, or network connection
is required.

## Build the complete showcase and dashboard

```powershell
iq4comm showcase all --output-dir showcase_output --require-cvxpy
```

The output directory contains:

```text
showcase_output/
├── index.html
├── iQuant4_showcase_standalone.html
├── dashboard_data.json
├── showcase_manifest.json
├── receiver_family/
├── lossy_cat/
└── sign_free_tomography/
```

Open the folder-relative dashboard:

```powershell
Start-Process .\showcase_output\index.html
```

Or generate and open it in one command:

```powershell
iq4comm showcase all --output-dir showcase_output --open
```

## Two HTML formats

- `index.html` references the generated PNG, JSON, CSV, and report artifacts by
  relative path. Keep it with the showcase directory.
- `iQuant4_showcase_standalone.html` embeds the scientific figures directly in
  the HTML file. It is convenient for sharing a visual preview as one file.

## Rebuild a dashboard from existing artifacts

```powershell
iq4comm showcase dashboard --output-dir showcase_output
```

This command reads `showcase_manifest.json` and the existing machine-readable
results. It does not rerun the scientific simulations.

## Python API

```python
from iq4comm.showcase import build_showcase_dashboard

result = build_showcase_dashboard("showcase_output")
print(result.html_path)
print(result.standalone_html_path)
```

The dashboard summarizes:

- the winning receiver family and BER at the longest evaluated distance;
- loss-induced changes in photon number, purity, and Wigner negativity;
- tomography status, fidelity, RMSE, and vectorization accuracy;
- the four-branch iQuant4 roadmap;
- the product principles of solutions, convenience, and experience.
