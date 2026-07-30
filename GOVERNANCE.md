# iQuant4 governance

## Project status

iQuant4 is currently a developer-alpha project led and maintained by
**Amir Yazdanpour**. The repository contains the shared `iqcore` engine and the
first active branch, `iq4comm`.

## Decision making

During the developer-alpha phase, the lead maintainer has final responsibility
for architecture, release scope, scientific conventions, and security
responses. Significant technical decisions should be documented in issues,
pull requests, architecture notes, or release documentation so that the
reasoning remains visible to future contributors.

## Contributions

Contributions are welcome through issues and pull requests after the repository
opens for external collaboration. Contributors must follow the code of conduct,
include tests for behavioral changes, preserve documented scientific
conventions, and avoid adding reverse dependencies from `iqcore` to product
branches.

## Releases

Releases follow semantic versioning. Pre-release versions may change APIs, but
all intentional public-API changes must be recorded in the changelog and the
public API documentation. A release is created only after the scientific,
architecture, packaging, documentation, and isolated-install gates pass.

## Security

Security reports follow `SECURITY.md`. Sensitive reports must not be filed as
public issues before coordinated disclosure has been discussed with the
maintainer.

## Future evolution

Governance will be revisited when the project gains additional maintainers or
active iQuant4 branches. At that point, maintainership areas, review authority,
and release responsibilities may be formalized by package or scientific domain.
