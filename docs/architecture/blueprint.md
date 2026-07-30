# iQuant4 Architecture Blueprint

## Workspace

`iQuant4` is a monorepo for a shared quantum-engineering foundation and four
application branches. During the first public-alpha cycle, only `iqcore` and
`iq4comm` are active packages.

```text
iQuant4/
├── iqcore/          shared scientific engine
├── iq4comm/         optical and quantum communications
├── tests/
├── examples/
├── docs/
└── archive/
```

Future product branches are planned as `iq4compute`, `iq4sense`, and
`iq4photonics`. They must depend on `iqcore`, never the reverse.

## Dependency rule

```text
iq4comm ─────► iqcore
```

Canonical `iqcore` modules must not import communication-specific modules or
legacy root wrappers. Legacy root modules may temporarily forward to canonical
package APIs for backward compatibility.

## iqcore ownership

- `states`: Fock, coherent, cat, GKP, squeezed, thermal, TMSV, density-matrix
  validation, tensor products, and partial traces.
- `operators`: reusable bosonic operators.
- `measurements`: quadrature theory, numerical sampling, and future POVMs.
- `channels`: application-independent quantum channels such as pure loss.
- `optics`: beam splitters, phase shifts, and OPA primitives.
- `phase_space`: Wigner functions and related representations.
- `metrics`: application-independent state statistics.
- `visualization`: plots of quantum states and shared scientific results.
- `tomography`: reconstruction algorithms and validation.

## iq4comm ownership

- coherent communication sources;
- system-level fiber and free-space propagation;
- receiver architectures and decision rules;
- BER, acceptance, erasure, and communication metrics;
- receiver and threshold optimization;
- QKD protocols, attacks, reconciliation, and key-rate analysis.

## Migration rules

1. One canonical implementation per scientific concept.
2. Canonical code imports only canonical package modules.
3. Legacy root files remain thin wrappers until the alpha API is stable.
4. Every migration includes smoke tests and regression tests.
5. Structural movement and public-API renaming are separate changes.
6. Tests run through the project interpreter: `.venv/Scripts/python.exe -m pytest`.

## Completed milestones

- Shared state library and validation.
- Bosonic operators.
- Quadrature measurement engine.
- Tensor-product and subsystem utilities.
- Beam-splitter physics.
- Wigner phase-space tools.
- Communication source/channel/receiver foundation.
- Pure-loss channels, phase shifts, sign-free OPA, attenuation, and numerical
  homodyne sampling.
- Photon-number metrics and shared state visualization.
- Sign-free POVMs, vectorized tomography, SDP reconstruction, and pure-state fidelity.
- Developer-alpha packaging metadata, versioning, architecture guards, and numerical conventions.

## First alpha scope

The first iQuant4 Developer Alpha will package `iqcore` and `iq4comm`, provide
end-to-end examples, run on Windows and Linux, and document known numerical
conventions and limitations. Compute, Sense, and Photonics remain roadmap
branches until after the first release.
