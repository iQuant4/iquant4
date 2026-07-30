# Future iQuant4 Branches

The first developer-alpha cycle actively develops `iqcore` and `iq4comm`.
The following product branches are architectural roadmaps rather than active
Python packages:

- **iQuant4Compute** — quantum computing, circuits, simulation, and error
  correction.
- **iQuant4Sense** — quantum sensing, imaging, estimation, and metrology.
- **iQuant4Photonics** — photonic devices, integrated optics, and physical
  component/system models.

Each future branch will depend on `iqcore`. No branch should cause `iqcore` to
depend on application-specific code.
