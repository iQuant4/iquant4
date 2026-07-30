"""Verify legal, metadata, documentation, and public-API release gates."""

from __future__ import annotations

import importlib
import sys
from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:  # Python 3.10
    import tomli as tomllib


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
ALLOWED_LICENSES = {"Apache-2.0", "MIT"}

PUBLIC_IMPORTS = {
    "iqcore.states": (
        "coherent_state",
        "fock_state",
        "even_cat_state",
        "density_matrix",
        "partial_trace",
    ),
    "iqcore.operators": ("annihilation_operator", "displacement_operator"),
    "iqcore.measurements": (
        "quadrature_statistics",
        "quadrature_probability_density",
    ),
    "iqcore.optics": ("apply_beam_splitter", "phase_shift_channel"),
    "iqcore.phase_space": ("wigner_function", "wigner_negativity"),
    "iqcore.tomography": ("reconstruct_density_matrix",),
    "iq4comm": (
        "BinaryCoherentSource",
        "FiberChannel",
        "HomodyneReceiver",
        "HeterodyneReceiver",
        "PNRReceiver",
        "optimize_receiver",
    ),
    "iq4comm.showcase": (
        "run_alpha_showcase",
        "run_lossy_cat_showcase",
        "run_receiver_family_showcase",
        "run_sign_free_tomography_showcase",
    ),
    "iq4comm.documentation": (
        "build_documentation_portal",
        "documentation_payload",
        "open_documentation_portal",
    ),
    "iq4comm.portal": (
        "build_public_preview",
        "open_public_preview",
    ),
}


def verify_release_gate() -> None:
    metadata = tomllib.loads(
        (PROJECT_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    )
    project = metadata["project"]
    license_expression = project.get("license")
    if license_expression not in ALLOWED_LICENSES:
        raise RuntimeError(f"unsupported or missing license: {license_expression!r}")
    if project.get("license-files") != ["LICENSE"]:
        raise RuntimeError("pyproject.toml must declare license-files = ['LICENSE']")

    license_text = (PROJECT_ROOT / "LICENSE").read_text(encoding="utf-8")
    if license_expression == "Apache-2.0" and "Apache License" not in license_text:
        raise RuntimeError("LICENSE does not contain the Apache-2.0 text")
    if license_expression == "MIT" and "Permission is hereby granted" not in license_text:
        raise RuntimeError("LICENSE does not contain the MIT text")

    citation = (PROJECT_ROOT / "CITATION.cff").read_text(encoding="utf-8")
    if f"license: {license_expression}" not in citation:
        raise RuntimeError("CITATION.cff license does not match pyproject.toml")

    readme = (PROJECT_ROOT / "README.md").read_text(encoding="utf-8")
    if "A release license has not yet been selected" in readme:
        raise RuntimeError("README still contains the pre-license placeholder")

    required_files = (
        "CONTRIBUTING.md",
        "SECURITY.md",
        "ROADMAP.md",
        "CODE_OF_CONDUCT.md",
        "GOVERNANCE.md",
        "docs/release/checklist.md",
        "docs/release/public_api.md",
        "docs/release/validation.md",
        "docs/release/showcase.md",
        "docs/release/documentation.md",
        "docs/release/public_preview.md",
        "docs/tutorials/alpha_showcase.md",
        "docs/development/repository.md",
        "docs/release/github.md",
        ".github/dependabot.yml",
        ".github/PULL_REQUEST_TEMPLATE.md",
        ".github/workflows/pages.yml",
        ".github/workflows/release-candidate.yml",
        ".github/ISSUE_TEMPLATE/bug_report.yml",
    )
    missing = [path for path in required_files if not (PROJECT_ROOT / path).is_file()]
    if missing:
        raise RuntimeError(f"release-gate files are missing: {missing}")

    for module_name, names in PUBLIC_IMPORTS.items():
        module = importlib.import_module(module_name)
        missing_names = [name for name in names if not hasattr(module, name)]
        if missing_names:
            raise RuntimeError(f"{module_name} is missing public names: {missing_names}")

    print("release gate passed")
    print(f"license: {license_expression}")
    print(f"version: {project['version']}")


def main() -> None:
    verify_release_gate()


if __name__ == "__main__":
    main()
