# Publishing the developer alpha

The first public upload should go to TestPyPI, not directly to production PyPI.

## Build and validate

```powershell
.\.venv\Scripts\python.exe -m pip install -e ".[release]"
.\.venv\Scripts\python.exe tools\generate_validation_report.py
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m build --wheel --sdist --outdir dist\candidate
.\.venv\Scripts\python.exe -m twine check dist\candidate\*
.\.venv\Scripts\python.exe tools\verify_release_candidate.py dist\candidate
```

## Upload to TestPyPI

Create the TestPyPI project/account configuration first, then run:

```powershell
.\.venv\Scripts\python.exe -m twine upload --repository testpypi dist\candidate\*
```

Install the uploaded build into a new environment and run diagnostics:

```powershell
python -m venv .testpypi-venv
.\.testpypi-venv\Scripts\python.exe -m pip install \
    --index-url https://test.pypi.org/simple/ \
    --extra-index-url https://pypi.org/simple/ \
    iq4comm==0.1.0a1
.\.testpypi-venv\Scripts\python.exe -m iq4comm doctor
```

The extra production-PyPI index is needed because TestPyPI is not intended to
mirror every runtime dependency.

## Production release

Do not upload to production PyPI until the release checklist is complete, the
remote CI matrix passes, the package name is confirmed, and the release commit
is frozen. Prefer PyPI Trusted Publishing from GitHub Actions once the public
repository and PyPI project are configured.

## Public preview

Before a broad package announcement, build and review the static portal described in [`public_preview.md`](public_preview.md). The GitHub Pages workflow is manual during the alpha period.
