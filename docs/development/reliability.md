# Alpha reliability and clean-install verification

The iQuant4 developer alpha uses three complementary quality layers.

## 1. Scientific and architecture tests

Run the complete test suite with the project interpreter:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

The suite covers numerical conventions, quantum-state operations, optical
transformations, tomography, communication receivers, public APIs, legacy
compatibility wrappers, and package architecture.

## 2. Runtime diagnostics

The unified command line exposes a lightweight doctor command:

```powershell
iq4comm doctor
```

For machine-readable output:

```powershell
iq4comm doctor --json
```

The diagnostic checks version synchronization, core dependencies, vacuum-state
normalization, the vacuum quadrature variance, and the 50 km fiber-loss
reference value.

## 3. Wheel and isolated-install verification

Build a wheel and verify it outside the source checkout:

```powershell
.\.venv\Scripts\python.exe -m pip wheel . --no-deps --no-build-isolation -w dist\candidate
.\.venv\Scripts\python.exe tools\verify_release_candidate.py dist\candidate
```

The verifier creates a temporary virtual environment, force-installs the wheel,
clears `PYTHONPATH`, runs package imports from a separate directory, exercises
`python -m iq4comm`, and runs the doctor command.

## Continuous integration

`.github/workflows/ci.yml` executes the same tests, wheel build, and isolated
installation checks on Windows and Ubuntu across supported Python versions.
