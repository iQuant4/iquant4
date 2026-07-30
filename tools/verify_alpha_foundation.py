from __future__ import annotations

import sys
try:
    import tomllib
except ModuleNotFoundError:  # Python 3.10
    import tomli as tomllib
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import iq4comm
import iqcore


def main() -> None:
    metadata = tomllib.loads(
        (PROJECT_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    )
    expected_version = metadata["project"]["version"]

    assert iqcore.__version__ == expected_version
    assert iq4comm.__version__ == expected_version
    assert iqcore.states.coherent_state is not None
    assert iqcore.measurements.quadrature_statistics is not None
    assert iqcore.optics.beam_splitter_unitary is not None
    assert iqcore.tomography.reconstruct_density_matrix is not None
    assert iq4comm.BinaryCoherentSource is not None
    assert iq4comm.ErasurePNRReceiver is not None
    from iq4comm.analysis import compare_receiver_families
    assert compare_receiver_families is not None

    print("alpha foundation smoke test passed")
    print(f"version: {expected_version}")


if __name__ == "__main__":
    main()
