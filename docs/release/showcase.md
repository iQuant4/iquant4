# Flagship showcase release gate

The developer-alpha announcement should demonstrate value through three
workflows rather than through a long feature inventory.

| Showcase | User problem solved | Primary artifacts |
|---|---|---|
| Receiver-family comparison | Select and optimize a receiver over distance | report, CSV, JSON, BER figure |
| Loss-degraded cat state | Understand how attenuation destroys nonclassicality | metrics, Wigner figure |
| Sign-free tomography | Reconstruct a quantum state from sign-free quadrature data | fidelity report, reconstruction figure |

A release candidate passes this gate when:

1. `iq4comm showcase all` completes in a clean installed environment;
2. `showcase_manifest.json` is created;
3. every completed component writes nonempty JSON and PNG artifacts;
4. tomography either completes or records an explicit optional-dependency skip;
5. no showcase imports a root-level compatibility wrapper.

These workflows map to the iQuant4 product roadmap:

- **Solutions:** receiver selection, loss analysis, and state reconstruction;
- **Convenience:** one command produces reports, data, and figures;
- **Experience:** polished visual artifacts communicate the underlying physics.

## Offline dashboard

The complete showcase also produces `index.html`, a responsive offline dashboard
that combines the three workflows, headline metrics, artifact links, and the
four-branch iQuant4 roadmap. `iQuant4_showcase_standalone.html` embeds the
principal PNG figures for one-file visual sharing. See
`docs/release/dashboard.md` for the release gate.
