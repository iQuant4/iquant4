# iQuant4 Roadmap

`iqcore` is the shared scientific engine. Four application branches are planned
under the iQuant4 umbrella.

## Active in the developer alpha

### iQuant4Comm (`iq4comm`)

- optical and quantum communication sources;
- fiber and attenuation models;
- PNR, homodyne, and heterodyne receiver families;
- receiver metrics and optimization;
- quantum-state analysis, tomography, dashboards, and documentation built on
  `iqcore`.

## Planned branches

### iQuant4Compute (`iq4compute`)

Quantum circuits, simulators, algorithms, control, and error correction.

### iQuant4Sense (`iq4sense`)

Quantum sensing, imaging, estimation, interferometry, and metrology.

### iQuant4Photonics (`iq4photonics`)

Photonic devices, integrated components, system models, and inverse design.

## Shared capability

AI and optimization are cross-cutting capabilities rather than a fifth branch.
They may appear inside each product branch while reusable numerical and data
interfaces remain in `iqcore`.

## Dependency rule

Application branches may depend on `iqcore`. `iqcore` must never depend on an
application branch. Shared functionality used by more than one branch should be
moved into `iqcore` rather than duplicated.

## Alpha priorities

1. Make the existing platform installable, reproducible, and understandable.
2. Validate the flagship scientific workflows against analytical or published
   reference results.
3. Invite a limited group of technical reviewers.
4. Stabilize the public API before broad feature expansion.
5. Begin the next branch only after iQuant4Comm has a credible user workflow.
