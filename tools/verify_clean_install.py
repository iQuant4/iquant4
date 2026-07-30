"""Verify an iQuant4 wheel from an isolated temporary environment."""

from __future__ import annotations

import json
import os
import site
import subprocess
import sys
import tempfile
from pathlib import Path


def _venv_python(venv_root: Path) -> Path:
    return (
        venv_root / "Scripts" / "python.exe"
        if os.name == "nt"
        else venv_root / "bin" / "python"
    )


def verify_clean_install(wheel_path: Path) -> None:
    """Install ``wheel_path`` into a temporary venv and run smoke checks.

    The temporary environment receives only dependency search paths from the
    current verified interpreter. The iQuant4 wheel itself is force-installed
    into the temporary environment and imported from a working directory
    outside the source checkout. Assertions ensure that ``iqcore`` and
    ``iq4comm`` resolve from the temporary environment, not those dependency
    paths or the source tree.
    """
    wheel = wheel_path.resolve()
    if not wheel.is_file():
        raise FileNotFoundError(wheel)

    with tempfile.TemporaryDirectory(prefix="iquant4_clean_install_") as temp:
        temp_root = Path(temp)
        venv_root = temp_root / "venv"
        run_root = temp_root / "run"
        run_root.mkdir()

        subprocess.run(
            [sys.executable, "-m", "venv", str(venv_root)],
            check=True,
        )
        python = _venv_python(venv_root)

        dependency_paths = [
            Path(path).resolve()
            for path in site.getsitepackages()
            if Path(path).is_dir()
        ]
        user_site = Path(site.getusersitepackages()).resolve()
        if user_site.is_dir():
            dependency_paths.append(user_site)

        site_result = subprocess.run(
            [
                str(python),
                "-c",
                "import site; print(site.getsitepackages()[0])",
            ],
            check=True,
            capture_output=True,
            text=True,
        )
        isolated_site_packages = Path(site_result.stdout.strip())
        dependency_file = isolated_site_packages / "iquant4_dependency_paths.pth"
        dependency_file.write_text(
            "".join(f"{path}\n" for path in dependency_paths),
            encoding="utf-8",
        )

        environment = os.environ.copy()
        environment.pop("PYTHONPATH", None)
        environment["PYTHONNOUSERSITE"] = "1"

        subprocess.run(
            [
                str(python),
                "-m",
                "pip",
                "install",
                "--no-deps",
                "--force-reinstall",
                str(wheel),
            ],
            cwd=run_root,
            env=environment,
            check=True,
        )

        smoke_path = run_root / "smoke.py"
        smoke_path.write_text(
            """
from __future__ import annotations

from importlib import metadata
from pathlib import Path
import sys

import numpy as np
import iq4comm
import iqcore
from iq4comm import BinaryCoherentSource, FiberChannel
from iqcore.states import fock_state

assert metadata.version("iq4comm") == iq4comm.__version__
assert iqcore.__version__ == iq4comm.__version__
assert Path(iq4comm.__file__).resolve().is_relative_to(Path(sys.prefix).resolve())
assert Path(iqcore.__file__).resolve().is_relative_to(Path(sys.prefix).resolve())
assert np.isclose(np.linalg.norm(fock_state(0, 8)), 1.0)
source = BinaryCoherentSource(mu_0=2.0, mu_1=8.0)
channel = FiberChannel(attenuation_db_per_km=0.2)
state = channel.propagate(
    mu=source.mean_photon_number(0),
    alpha=source.amplitude(0),
    distance_km=50.0,
)
assert np.isclose(state.transmittance, 0.1)
print("isolated package imports passed")
""".lstrip(),
            encoding="utf-8",
        )
        subprocess.run(
            [str(python), str(smoke_path)],
            cwd=run_root,
            env=environment,
            check=True,
        )

        version_result = subprocess.run(
            [str(python), "-m", "iq4comm", "--version"],
            cwd=run_root,
            env=environment,
            check=True,
            capture_output=True,
            text=True,
        )
        if version_result.stdout.strip() != metadata_version(wheel):
            raise RuntimeError(
                "installed CLI version does not match wheel filename/version"
            )

        doctor_result = subprocess.run(
            [str(python), "-m", "iq4comm", "doctor", "--json"],
            cwd=run_root,
            env=environment,
            check=True,
            capture_output=True,
            text=True,
        )
        doctor = json.loads(doctor_result.stdout)
        if not doctor.get("healthy"):
            raise RuntimeError(f"installed doctor reported failure: {doctor}")

        showcase_root = run_root / "showcase"
        subprocess.run(
            [
                str(python),
                "-m",
                "iq4comm",
                "showcase",
                "all",
                "--skip-tomography",
                "--output-dir",
                str(showcase_root),
            ],
            cwd=run_root,
            env=environment,
            check=True,
        )
        showcase_json = showcase_root / "lossy_cat" / "lossy_cat_metrics.json"
        showcase_png = showcase_root / "lossy_cat" / "lossy_cat_wigner.png"
        dashboard_html = showcase_root / "index.html"
        standalone_html = showcase_root / "iQuant4_showcase_standalone.html"
        dashboard_data = showcase_root / "dashboard_data.json"
        required_showcase_files = (
            showcase_json,
            showcase_png,
            dashboard_html,
            standalone_html,
            dashboard_data,
        )
        if any(
            not path.is_file() or path.stat().st_size == 0
            for path in required_showcase_files
        ):
            raise RuntimeError("installed showcase did not create expected artifacts")
        if showcase_png.read_bytes()[:8] != b"\x89PNG\r\n\x1a\n":
            raise RuntimeError("installed showcase created an invalid PNG artifact")
        dashboard_text = dashboard_html.read_text(encoding="utf-8")
        if "iQuant4 Developer Alpha Showcase" not in dashboard_text:
            raise RuntimeError("installed showcase dashboard is invalid")
        if "http://" in dashboard_text or "https://" in dashboard_text:
            raise RuntimeError("installed showcase dashboard requires external assets")

        portal_root = run_root / "public_preview"
        subprocess.run(
            [
                str(python),
                "-m",
                "iq4comm",
                "portal",
                "build",
                "--output-dir",
                str(portal_root),
                "--skip-showcase",
            ],
            cwd=run_root,
            env=environment,
            check=True,
        )
        required_portal_files = (
            portal_root / "index.html",
            portal_root / "roadmap.html",
            portal_root / "portal_manifest.json",
            portal_root / "docs" / "index.html",
        )
        if any(
            not path.is_file() or path.stat().st_size == 0
            for path in required_portal_files
        ):
            raise RuntimeError(
                "installed public-preview portal did not create expected artifacts"
            )
        portal_text = (portal_root / "index.html").read_text(encoding="utf-8")
        if "iQuant4" not in portal_text or "Developer-alpha scope" not in portal_text:
            raise RuntimeError("installed public-preview portal is invalid")
        if "http://" in portal_text or "https://" in portal_text:
            raise RuntimeError("installed public-preview portal requires external assets")

    print("clean wheel install passed")
    print(wheel)


def metadata_version(wheel_path: Path) -> str:
    """Extract the normalized version from an iq4comm wheel filename."""
    name = wheel_path.name
    prefix = "iq4comm-"
    if not name.startswith(prefix) or not name.endswith(".whl"):
        raise ValueError(f"unexpected wheel name: {name}")
    return name[len(prefix) :].split("-", 1)[0]


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("usage: verify_clean_install.py <wheel-path>")
    verify_clean_install(Path(sys.argv[1]))


if __name__ == "__main__":
    main()
