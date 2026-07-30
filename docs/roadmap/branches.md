# iQuant4 Branch Roadmap

## Shared foundation

`iqcore` is the application-independent foundation. It owns reusable quantum
states, operators, subsystem algebra, measurements, channels, optics,
phase-space representations, metrics, tomography, and numerical utilities.

## Four application branches

1. **iQuant4Comm** (`iq4comm`) — active. Optical and quantum communications,
   receiver families, propagation, metrics, optimization, and future QKD.
2. **iQuant4Compute** (`iq4compute`) — planned. Computing, circuits,
   algorithms, simulation, and error correction.
3. **iQuant4Sense** (`iq4sense`) — planned. Sensing, imaging, estimation, and
   metrology.
4. **iQuant4Photonics** (`iq4photonics`) — planned. Photonic components,
   devices, integrated systems, and inverse design.

## Dependency law

```text
iq4comm       ─┐
iq4compute     │
iq4sense       ├──► iqcore
iq4photonics  ─┘
```

The reverse dependency is forbidden. Shared functionality discovered in an
application branch should be promoted into `iqcore` only after its interface is
shown to be reusable.

## First release

The first iQuant4 Developer Alpha implements `iqcore` and `iq4comm`. The other
three branches remain documented roadmaps until after the alpha release.
