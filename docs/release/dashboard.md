# Offline dashboard release gate

The iQuant4 developer alpha must provide a visual entry point for people who do
not begin by reading Python source code or JSON files.

A release candidate passes the dashboard gate when:

1. `iq4comm showcase all` creates `index.html` automatically;
2. the dashboard uses only local assets and contains no external network
   dependencies;
3. the receiver-family and lossy-cat figures are visible;
4. completed tomography metrics and figures are included when available;
5. skipped optional tomography is explained transparently;
6. all raw CSV, JSON, text, and PNG artifacts remain directly accessible;
7. a standalone HTML file embeds the principal figures;
8. the installed wheel can generate the same dashboard outside the source
   checkout.

The dashboard is a presentation layer over verified machine-readable artifacts.
It does not replace the scientific validation report, raw data, or documented
model assumptions.
