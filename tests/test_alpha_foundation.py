from __future__ import annotations

import ast
try:
    import tomllib
except ModuleNotFoundError:  # Python 3.10
    import tomli as tomllib
from pathlib import Path

import iq4comm
import iqcore


PROJECT_ROOT = Path(__file__).resolve().parents[1]
CANONICAL_ROOTS = (PROJECT_ROOT / "iqcore", PROJECT_ROOT / "iq4comm")
LEGACY_MODULES = {
    "beam_splitter",
    "channel",
    "heterodyne",
    "homodyne",
    "metrics",
    "multimode",
    "opa",
    "optical_channels",
    "optimizer",
    "performance",
    "phase_space",
    "pnr",
    "quadrature",
    "quadrature_measurement",
    "quantum_state_tools",
    "quantum_states",
    "receiver",
    "sign_free_tomography",
    "source",
    "state",
    "visualization",
}


def imported_roots(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8-sig"), filename=str(path))
    roots: set[str] = set()

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            roots.update(alias.name.split(".", 1)[0] for alias in node.names)
        elif (
            isinstance(node, ast.ImportFrom)
            and node.level == 0
            and node.module
        ):
            roots.add(node.module.split(".", 1)[0])

    return roots


def canonical_python_files() -> list[Path]:
    return [
        path
        for root in CANONICAL_ROOTS
        for path in root.rglob("*.py")
        if "__pycache__" not in path.parts
    ]


def test_canonical_packages_do_not_import_legacy_root_modules() -> None:
    violations: dict[str, list[str]] = {}

    for path in canonical_python_files():
        forbidden = sorted(imported_roots(path) & LEGACY_MODULES)
        if forbidden:
            violations[str(path.relative_to(PROJECT_ROOT))] = forbidden

    assert violations == {}


def test_iqcore_does_not_depend_on_iq4comm() -> None:
    violations = [
        str(path.relative_to(PROJECT_ROOT))
        for path in (PROJECT_ROOT / "iqcore").rglob("*.py")
        if "iq4comm" in imported_roots(path)
    ]

    assert violations == []


def test_distribution_metadata_and_package_discovery() -> None:
    metadata = tomllib.loads(
        (PROJECT_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    )

    assert metadata["project"]["name"] == "iq4comm"
    assert metadata["project"]["version"] == "0.2.0a1"
    assert metadata["project"]["requires-python"] == ">=3.10"
    assert metadata["tool"]["setuptools"]["packages"]["find"]["include"] == [
        "iqcore*",
        "iq4comm*",
    ]


def test_public_versions_match_distribution_version() -> None:
    assert iqcore.__version__ == "0.2.0a1"
    assert iq4comm.__version__ == iqcore.__version__


def test_iqcore_lazy_public_namespaces() -> None:
    assert iqcore.states.coherent_state is not None
    assert iqcore.measurements.quadrature_statistics is not None
    assert iqcore.optics.beam_splitter_unitary is not None
    assert iqcore.phase_space.wigner_function is not None
    assert iqcore.tomography.reconstruct_density_matrix is not None


def test_legacy_compatibility_wrappers_remain_importable() -> None:
    from beam_splitter import apply_beam_splitter
    from phase_space import wigner_function
    from quadrature_measurement import quadrature_statistics
    from quantum_states import coherent_state
    from sign_free_tomography import reconstruct_density_matrix

    assert all(
        callable(value)
        for value in (
            apply_beam_splitter,
            coherent_state,
            quadrature_statistics,
            reconstruct_density_matrix,
            wigner_function,
        )
    )


def test_readme_documents_alpha_installation_and_architecture() -> None:
    readme = (PROJECT_ROOT / "README.md").read_text(encoding="utf-8")

    assert "Developer Alpha" in readme
    assert 'pip install -e ".[dev,tomography]"' in readme
    assert "iqcore" in readme
    assert "iq4comm" in readme
