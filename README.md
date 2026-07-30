# iQuant4 Developer Alpha

**iQuant4** is an emerging quantum-engineering workspace. The first developer
alpha contains two active Python packages:

- **`iqcore`** — reusable quantum states, operators, measurements, optical
  transformations, phase-space tools, metrics, and tomography.
- **`iq4comm`** — coherent optical sources, fiber channels, receiver models,
  receiver metrics, and threshold optimization for optical and quantum
  communications.

The future iQuant4 roadmap includes **iQuant4Compute**, **iQuant4Sense**, and
**iQuant4Photonics**. They will build on `iqcore`; they are documented under
[`branches/`](branches/) but are not active Python packages in this alpha.

## Status

This repository is a **developer alpha (`0.1.0a1`)**. APIs may still change.
The current implementation uses truncated Fock spaces and asymptotic or
idealized models in several places. It is a research and engineering toolkit,
not a claim of complete physical-device or composable-security coverage.

## Install from source

Create and activate a virtual environment, then install the communication
package together with tomography and development dependencies:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev,tomography]"
```

On macOS or Linux, use `.venv/bin/python` instead.

## Quick start: shared quantum engine

```python
import numpy as np
import iqcore as iq

state = iq.states.even_cat_state(alpha=1.5, cutoff=30)
grid = np.linspace(-5.0, 5.0, 151)
wigner = iq.phase_space.wigner_function(state, grid, grid)

print(iq.metrics.mean_photon_number(state))
print(iq.phase_space.wigner_normalization(wigner, grid, grid))
```

## Quick start: communication receiver

```python
import iq4comm as iqc

source = iqc.BinaryCoherentSource(mu_0=2.0, mu_1=8.0)
channel = iqc.FiberChannel(attenuation_db_per_km=0.2)

state_0 = channel.propagate(
    mu=source.mean_photon_number(0),
    alpha=source.amplitude(0),
    distance_km=20.0,
)
state_1 = channel.propagate(
    mu=source.mean_photon_number(1),
    alpha=source.amplitude(1),
    distance_km=20.0,
)

receiver = iqc.ErasurePNRReceiver(
    lower_threshold=1,
    upper_threshold=3,
)
metrics = receiver.analytical_metrics(state_0, state_1)
print(metrics)
```


## Unified command line and diagnostics

After installation, the developer alpha exposes a unified command:

```powershell
iq4comm --version
iq4comm doctor
iq4comm receiver-family --distances 0 20 40 --threshold-step 0.1
```

The same interface is available without relying on a console-script launcher:

```powershell
python -m iq4comm doctor --json
```

The doctor command checks package-version synchronization, scientific
dependencies, basic quantum-state invariants, and a reference fiber-loss
calculation. It is intended for installation reports and reproducible bug
reports.

## Flagship developer-alpha showcase

Generate three reproducible reports and figures with one command:

```powershell
iq4comm showcase all --output-dir showcase_output
```

The showcase includes receiver-family optimization, loss-degraded cat-state
Wigner analysis, and optional sign-free tomography. It writes a JSON manifest,
CSV data, text reports, PNG figures, and an offline HTML dashboard:

```powershell
Start-Process .\showcase_output\index.html
```

A standalone HTML version embeds the principal figures for convenient sharing.
See [`docs/tutorials/alpha_showcase.md`](docs/tutorials/alpha_showcase.md) and
[`docs/tutorials/showcase_dashboard.md`](docs/tutorials/showcase_dashboard.md).

## One-command receiver-family comparison

The developer alpha includes a reusable analysis API and a command-line demo
that optimizes erasure PNR, homodyne, and heterodyne receiver families under a
common minimum-acceptance constraint:

```powershell
iq4comm-receiver-family --distances 0 20 40 --threshold-step 0.1
```

From a source checkout, run the same analysis with:

```powershell
.\.venv\Scripts\python.exe -m iq4comm.analysis.receiver_family `
    --distances 0 20 40 `
    --threshold-step 0.1
```

A headless example spanning both active packages is available at
[`examples/alpha_quickstart.py`](examples/alpha_quickstart.py), with a guided
walkthrough in
[`docs/tutorials/alpha_quickstart.md`](docs/tutorials/alpha_quickstart.md).

## Scientific conventions

The main numerical conventions—including quadrature normalization, Fock-space
cutoffs, tensor ordering, beam-splitter phases, and Wigner normalization—are
documented in [`docs/architecture/conventions.md`](docs/architecture/conventions.md).

## Reliability and continuous integration

The repository includes Windows and Ubuntu continuous integration across
Python 3.10–3.14. Every CI job runs the scientific suite, builds the wheel, and
installs that wheel into an isolated temporary environment outside the source
checkout. See
[`docs/development/reliability.md`](docs/development/reliability.md) for the
local verification commands.

## Test suite

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

## Release preparation

The supported alpha API, validation report, publishing guide, and release checklist are documented under [`docs/release/`](docs/release/). Contributors should also read [`CONTRIBUTING.md`](CONTRIBUTING.md) and [`SECURITY.md`](SECURITY.md).


## Static public preview

Build one offline-ready folder containing the iQuant4 landing page, installed
documentation, product roadmap, and flagship showcase:

```powershell
iq4comm portal build --output-dir public_preview --open
```

Include sign-free SDP tomography when CVXPY is installed:

```powershell
iq4comm portal build `
    --output-dir public_preview `
    --include-tomography `
    --require-cvxpy `
    --open
```

The output can be reviewed locally or deployed as an ordinary static website.
A manual GitHub Pages workflow is documented in
[`docs/release/public_preview.md`](docs/release/public_preview.md).

## Repository workflow

The developer alpha includes Git hygiene checks, dependency update automation,
CI, a manual release-candidate workflow, and a documented GitHub launch path.
See [`docs/development/repository.md`](docs/development/repository.md) for the
branch and commit workflow and [`docs/release/github.md`](docs/release/github.md)
for the private-preview and public-launch checklist.

Run the local repository gate with:

```powershell
python tools/verify_repository_hygiene.py --root . --require-git
```

## Repository architecture

```text
iQuant4/
├── iqcore/       shared scientific engine
├── iq4comm/      communications branch
├── tests/        scientific and architecture regression tests
├── examples/     runnable demonstrations
└── docs/         architecture and numerical conventions
```

## License

This developer alpha is distributed under the **Apache-2.0** license. See the root [`LICENSE`](LICENSE) file and [`docs/release/licensing.md`](docs/release/licensing.md).

## Installed offline documentation

Build a self-contained documentation portal directly from an installed wheel:

```powershell
iq4comm docs build --output-dir documentation_output
Start-Process .\documentation_output\index.html
```

The portal includes a five-minute quick start, flagship workflow guides,
scientific limitations, local search, and generated API inventories for both
`iqcore` and `iq4comm`. It uses only local HTML, CSS, JavaScript, and JSON
artifacts and can be opened through `file://` without a web server.
