# Public preview and GitHub Pages

The developer alpha can generate one static folder containing:

- the iQuant4 landing page and roadmap;
- installed offline documentation;
- the flagship iQuant4Comm showcase dashboard;
- machine-readable manifests and scientific artifacts.

## Local build

```powershell
iq4comm portal build --output-dir public_preview --open
```

Include SDP tomography when CVXPY is installed:

```powershell
iq4comm portal build `
    --output-dir public_preview `
    --include-tomography `
    --require-cvxpy `
    --open
```

A fast documentation-only build is available with:

```powershell
iq4comm portal build --output-dir public_preview --skip-showcase
```

The generated folder is fully static and can be copied to any ordinary static
host. No web server or remote JavaScript/CSS dependency is required.

## GitHub Pages

The repository contains `.github/workflows/pages.yml`. It is intentionally
manual during the alpha period. After the repository is pushed to GitHub:

1. Open **Settings → Pages**.
2. Select **GitHub Actions** as the source.
3. Open **Actions → iQuant4 Public Preview**.
4. Run the workflow manually.
5. Review the deployed URL before sharing it publicly.

The workflow installs the released source, generates documentation and the fast
showcase without SDP tomography, uploads the static artifact, and deploys it to
GitHub Pages.

## Release rule

Do not treat the public preview as evidence of complete physical-device or
security coverage. Keep the developer-alpha limitation notice visible until the
scope changes and the corresponding validation is complete.
