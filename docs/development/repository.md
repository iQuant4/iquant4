# Repository workflow

This document defines the development workflow for the iQuant4 monorepo.
The repository contains two active Python packages:

- `iqcore`: the shared scientific engine;
- `iq4comm`: the optical and quantum communications branch.

The future iQuant4Compute, iQuant4Sense, and iQuant4Photonics branches are
roadmap items and are not active Python packages in the current alpha.

## Repository rules

1. iqcore must never import from `iq4comm`.
2. Canonical packages must not import legacy root wrappers.
3. Generated sites, wheels, logs, migration patches, virtual environments,
   archives, credentials, and private data must never be committed.
4. The `main` branch must remain installable and pass the complete test suite.
5. Every public API change must update tests, documentation, and the changelog.
6. Release artifacts are built by automation; they are not committed to Git.

The repository enforces these rules with:

```powershell
python tools/verify_repository_hygiene.py --root . --require-git
python -m pytest -q
```

## Branch naming

Use short, descriptive branches:

```text
feature/<topic>
fix/<topic>
docs/<topic>
refactor/<topic>
release/<version>
```

Examples:

```text
feature/pnr-dark-counts
fix/gkp-cutoff-validation
docs/tomography-tutorial
release/0.1.0a2
```

## Commit messages

Use imperative, scoped messages when practical:

```text
feat(iq4comm): add receiver-family export
fix(iqcore): preserve trace under pure loss
docs: explain tensor ordering
test: add GKP convergence regression
chore: update release metadata
```

A commit should represent one coherent change and include its tests.

## Local development cycle

```powershell
python -m pytest -q
python tools/verify_repository_hygiene.py --root . --require-git
python -m iq4comm doctor
```

Before a pull request, also build and validate the release artifacts:

```powershell
python -m build --wheel --sdist --outdir dist/local-check
python -m twine check dist/local-check/*
python tools/verify_release_candidate.py dist/local-check
```

## Main-branch protection

After the GitHub repository is created, enable branch protection for `main`:

- require a pull request before merging;
- require the `iQuant4 CI` checks to pass;
- require branches to be up to date before merging;
- block force pushes and branch deletion;
- dismiss approvals when new commits are pushed once external contributors
  begin participating.

During the initial solo-development period, direct commits may be used
sparingly for recovery or infrastructure work, but feature development should
move to pull requests as soon as the remote CI is active.

## Private preview versus public repository

The repository may remain private during the first external review. A private
preview is useful for validating installation, documentation, and scientific
results with trusted researchers before the public developer-alpha launch.

Before switching the repository to public visibility, complete the checklist
in [`../release/github.md`](../release/github.md).
