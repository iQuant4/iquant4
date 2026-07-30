"""Runtime diagnostics for the iQuant4 developer alpha.

The doctor command intentionally checks a small set of stable scientific and
packaging invariants. It is designed for users reporting installation or
runtime problems and for clean-install verification in continuous integration.
"""

from __future__ import annotations

import json
import platform
import sys
from dataclasses import asdict, dataclass
from importlib import metadata
from importlib.util import find_spec
from typing import Any

import numpy as np

from iqcore import __version__ as core_version
from iqcore.measurements import quadrature_statistics
from iqcore.states import fock_state

from ._version import __version__
from .channels import fiber_transmissivity


@dataclass(frozen=True, slots=True)
class DiagnosticCheck:
    """One diagnostic check and its human-readable result."""

    name: str
    passed: bool
    detail: str


@dataclass(frozen=True, slots=True)
class DiagnosticReport:
    """Structured result returned by :func:`run_diagnostics`."""

    iq4comm_version: str
    iqcore_version: str
    python_version: str
    platform: str
    dependencies: dict[str, str]
    optional_features: dict[str, str]
    checks: tuple[DiagnosticCheck, ...]

    @property
    def healthy(self) -> bool:
        """Return ``True`` when every required check passes."""
        return all(check.passed for check in self.checks)

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-serializable representation."""
        payload = asdict(self)
        payload["healthy"] = self.healthy
        return payload


def _distribution_version(name: str) -> str:
    try:
        return metadata.version(name)
    except metadata.PackageNotFoundError:
        return "not-installed-as-distribution"


def _check(name: str, condition: bool, detail: str) -> DiagnosticCheck:
    return DiagnosticCheck(name=name, passed=bool(condition), detail=detail)


def run_diagnostics() -> DiagnosticReport:
    """Run lightweight installation and scientific smoke checks."""
    dependencies = {
        package: _distribution_version(package)
        for package in ("numpy", "scipy", "matplotlib")
    }
    optional_features = {
        "cvxpy": (
            _distribution_version("cvxpy")
            if find_spec("cvxpy") is not None
            else "not-installed"
        )
    }

    vacuum = fock_state(photon_number=0, cutoff=8)
    vacuum_statistics = quadrature_statistics(vacuum, angle=0.0)
    fiber_eta = fiber_transmissivity(
        distance_km=50.0,
        loss_db_per_km=0.2,
    )

    checks = (
        _check(
            "version-sync",
            core_version == __version__,
            f"iqcore={core_version}, iq4comm={__version__}",
        ),
        _check(
            "vacuum-normalization",
            np.isclose(np.linalg.norm(vacuum), 1.0, atol=1e-12),
            f"norm={np.linalg.norm(vacuum):.12g}",
        ),
        _check(
            "vacuum-quadrature-variance",
            np.isclose(vacuum_statistics.variance, 0.5, atol=1e-12),
            f"variance={vacuum_statistics.variance:.12g}",
        ),
        _check(
            "fiber-transmissivity",
            np.isclose(fiber_eta, 0.1, atol=1e-12),
            f"eta_50km={fiber_eta:.12g}",
        ),
    )

    return DiagnosticReport(
        iq4comm_version=__version__,
        iqcore_version=core_version,
        python_version=platform.python_version(),
        platform=platform.platform(),
        dependencies=dependencies,
        optional_features=optional_features,
        checks=checks,
    )


def format_diagnostic_report(report: DiagnosticReport) -> str:
    """Format a diagnostic report for terminal output."""
    lines = [
        "iQuant4Comm Doctor",
        "==================",
        f"Status       : {'HEALTHY' if report.healthy else 'FAILED'}",
        f"iq4comm      : {report.iq4comm_version}",
        f"iqcore       : {report.iqcore_version}",
        f"Python       : {report.python_version}",
        f"Platform     : {report.platform}",
        "Dependencies : "
        + ", ".join(
            f"{name}={version}"
            for name, version in sorted(report.dependencies.items())
        ),
        "Optional     : "
        + ", ".join(
            f"{name}={version}"
            for name, version in sorted(report.optional_features.items())
        ),
        "",
        "Checks",
        "------",
    ]
    lines.extend(
        f"[{'PASS' if check.passed else 'FAIL'}] {check.name}: {check.detail}"
        for check in report.checks
    )
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    """Run the doctor command and return a process exit code."""
    arguments = list(sys.argv[1:] if argv is None else argv)
    unknown = [argument for argument in arguments if argument != "--json"]
    if unknown:
        raise SystemExit(f"unrecognized doctor arguments: {' '.join(unknown)}")

    report = run_diagnostics()
    if "--json" in arguments:
        print(json.dumps(report.to_dict(), indent=2, sort_keys=True))
    else:
        print(format_diagnostic_report(report))
    return 0 if report.healthy else 1


__all__ = [
    "DiagnosticCheck",
    "DiagnosticReport",
    "format_diagnostic_report",
    "main",
    "run_diagnostics",
]
