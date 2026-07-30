# Changelog

## 0.1.0a1 — Developer alpha in progress

### Added

- Shared `iqcore` state, operator, measurement, optics, phase-space, metrics,
  visualization, channel, and tomography namespaces.
- `iq4comm` coherent sources, fiber channels, receiver families, metrics, and
  receiver optimization.
- Backward-compatible wrappers for the original research modules.
- Scientific regression tests and architecture guards.
- Initial packaging metadata and developer-alpha documentation.
- Reusable receiver-family comparison API for erasure PNR, homodyne, and
  heterodyne receiver optimization.
- `iq4comm-receiver-family` command-line entry point.
- Headless alpha quick start and receiver-family tutorial.
- Unified `iq4comm` command with `doctor` and `receiver-family` subcommands.
- Runtime installation diagnostics with text and JSON reports.
- Isolated wheel-install verification outside the source checkout.
- Windows and Ubuntu continuous-integration workflow across Python 3.10–3.14.
- Python 3.10-compatible TOML parsing in development tests and verification tools.
### Release hardening

- Added selectable Apache-2.0 or MIT licensing with PEP 639 metadata.
- Added contribution, security, citation, public-API, validation, and release
  checklist documentation.
- Added wheel and source-distribution release-gate verification.
- Added issue and pull-request templates and repository-hygiene rules.
- Added generated scientific validation reporting.
- Added the `iq4comm showcase` command and reusable showcase API.
- Added receiver-family CSV/JSON/figure artifacts.
- Added loss-degraded cat-state metrics and Wigner gallery.
- Added an optional quick sign-free tomography showcase.
- Added flagship-showcase documentation and release gates.
- Added a responsive offline showcase dashboard with folder-relative and
  standalone embedded-image HTML outputs.
- Added `iq4comm showcase dashboard` and the `--open` showcase option.
- Added dashboard summaries for receiver optimization, Wigner negativity, and
  sign-free tomography, plus the four-branch iQuant4 roadmap.

### Installed documentation portal

- Added `iq4comm docs build` and `iq4comm docs open`.
- Added a responsive, offline documentation portal generated from installed packages.
- Added searchable public API inventories for `iqcore` and `iq4comm`.
- Added isolated-wheel verification for documentation generation.

### Public-preview portal

- Added `iq4comm portal build/open` for one-folder static publication.
- Added an offline landing page that links installed documentation and showcase artifacts.
- Added a manual GitHub Pages deployment workflow.
- Added the public roadmap, community code of conduct, and preview release guide.

### Repository readiness

- Added repository-hygiene verification for staged and tracked files.
- Added Git workflow, governance, GitHub launch, and branch-protection guidance.
- Added Dependabot configuration for Python and GitHub Actions dependencies.
- Added a manual release-candidate workflow that builds and verifies artifacts
  without publishing them.
- Added stricter ignore rules for virtual environments, migration bundles,
  generated portals, credentials, private keys, and local research data.
