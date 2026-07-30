# Contributing to iQuant4

Thank you for helping improve the iQuant4 developer alpha. The active packages
in this repository are `iqcore` and `iq4comm`.

## Development setup

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev,tomography,release]"
```

On macOS or Linux, use `.venv/bin/python`.

## Before submitting a change

Run the complete test suite and release diagnostics:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m iq4comm doctor
```

Changes to scientific conventions must include:

1. a clear mathematical definition;
2. at least one analytical or independently verifiable reference case;
3. regression tests;
4. an update to the relevant documentation.

## Architecture rules

- `iqcore` must never import from `iq4comm`.
- Canonical packages must not import legacy root-level compatibility modules.
- Application-independent quantum functionality belongs in `iqcore`.
- Communication-specific functionality belongs in `iq4comm`.
- Public imports should come from package namespaces such as
  `iqcore.states` and `iq4comm.receivers`.

## Compatibility wrappers

The root-level modules are migration aids for the source checkout. They are not
part of the installed wheel's supported public API. New code must not import
from them.


## Git workflow

Create a focused branch before changing code:

```powershell
git switch -c feature/<topic>
```

Use the branch and commit conventions documented in
[`docs/development/repository.md`](docs/development/repository.md). Before a
pull request, run the repository hygiene check in addition to the scientific
suite:

```powershell
python tools/verify_repository_hygiene.py --root . --require-git
python -m pytest -q
```

Never commit virtual environments, generated portals, release artifacts,
migration patches, credentials, private keys, or private research data.

## Reporting bugs

Include the output of:

```powershell
iq4comm doctor --json
```

along with the operating system, Python version, minimal reproducer, expected
result, and actual result.
