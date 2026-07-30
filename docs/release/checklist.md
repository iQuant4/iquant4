# iQuant4 developer-alpha release checklist

## Legal and project identity

- [ ] Selected license is present in `LICENSE` and `pyproject.toml`.
- [ ] Copyright holder and project author information are correct.
- [ ] Public repository name and organization are finalized.
- [ ] Public repository contact and security-reporting path are configured.

## Scientific quality

- [ ] Full scientific and architecture test suite passes.
- [ ] `docs/release/validation.md` was regenerated from the release candidate.
- [ ] Numerical conventions are documented.
- [ ] Known limitations are explicit in the README and tutorials.
- [ ] Three flagship showcase workflows run from a clean environment.
- [ ] `showcase_manifest.json` and all expected data/figure artifacts are generated.
- [ ] `index.html` and the standalone showcase dashboard are generated and open offline.

## Packaging

- [ ] Wheel and source distribution build successfully.
- [ ] `twine check` passes for all artifacts.
- [ ] Wheel content verification passes.
- [ ] Source-distribution content verification passes.
- [ ] Clean isolated wheel installation passes.
- [ ] `iq4comm doctor` reports `HEALTHY` after installation.

## Repository

- [ ] Git repository is initialized on `main` and the working tree is clean.
- [ ] `tools/verify_repository_hygiene.py --require-git --require-clean` passes.
- [ ] No generated artifacts, migration bundles, credentials, or oversized files are tracked.
- [ ] Dependabot is enabled for Python and GitHub Actions dependencies.
- [ ] GitHub Actions passes on Windows and Ubuntu.
- [ ] Main branch protection is enabled.
- [ ] Migration folders, local environments, caches, logs, and private data are
      not committed.
- [ ] Issue and pull-request templates are present.
- [ ] The manual release-candidate workflow builds and uploads verified artifacts.
- [ ] Repository governance and GitHub launch documentation are current.

## Publication

- [ ] TestPyPI upload succeeds.
- [ ] Installation from TestPyPI is verified in a new environment.
- [ ] Release notes and changelog are finalized.
- [ ] Version tag is created only after the release commit is frozen.
- [ ] Public announcement links to documentation, examples, and limitations.

## Installed documentation

- [ ] `iq4comm docs build` succeeds from an isolated wheel installation.
- [ ] Documentation portal uses only local runtime assets.
- [ ] Generated API inventories contain the expected public symbols.
- [ ] Search index and documentation manifest are generated.

## Public preview

- [ ] Build `iq4comm portal build --output-dir public_preview`.
- [ ] Review documentation and showcase links from the generated landing page.
- [ ] Run the manual GitHub Pages workflow and review the deployed URL.
- [ ] Keep the developer-alpha scope and limitations visible.
