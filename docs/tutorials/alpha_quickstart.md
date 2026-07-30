# iQuant4 Developer Alpha Quick Start

The first iQuant4 developer alpha exposes two active packages:

- `iqcore` for reusable quantum states, operators, measurements, optics,
  phase-space analysis, metrics, and tomography;
- `iq4comm` for coherent communication sources, fiber links, receiver models,
  and receiver optimization.

## Run the headless quick start

From the repository root:

```powershell
.\.venv\Scripts\python.exe .\examples\alpha_quickstart.py
```

The example constructs an even cat state, evaluates its Wigner normalization,
propagates a binary coherent source through 20 km of fiber, and evaluates an
erasure-PNR receiver.

## Compare receiver families

The installed developer alpha provides a command-line entry point:

```powershell
iq4comm-receiver-family --distances 0 20 40 --threshold-step 0.1
```

From a source checkout, the equivalent command is:

```powershell
.\.venv\Scripts\python.exe -m iq4comm.analysis.receiver_family `
    --distances 0 20 40 `
    --threshold-step 0.1
```

The command optimizes erasure PNR, homodyne, and heterodyne receiver families
subject to a common minimum-acceptance constraint. Reported BER values are
conditional on accepted observations.

## Scientific scope

The quick-start receiver comparison is an asymptotic analytical model for
binary coherent states under pure fiber attenuation. It is not a complete
security proof, hardware digital twin, or finite-key QKD analysis.
