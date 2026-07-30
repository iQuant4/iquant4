"""Source-checkout smoke test for ALPHA-RELIABILITY-08."""

from __future__ import annotations

import json
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from iq4comm import __version__
from iq4comm.cli import main as cli_main
from iq4comm.diagnostics import run_diagnostics


def main() -> None:
    report = run_diagnostics()
    assert report.healthy
    assert report.iq4comm_version == __version__
    assert report.iqcore_version == __version__
    assert cli_main(["--version"]) == 0

    workflow = PROJECT_ROOT / ".github" / "workflows" / "ci.yml"
    assert workflow.is_file()
    workflow_text = workflow.read_text(encoding="utf-8")
    assert "ubuntu-latest" in workflow_text
    assert "windows-latest" in workflow_text
    assert "verify_release_candidate.py" in workflow_text

    print("alpha reliability smoke test passed")
    print(json.dumps(report.to_dict(), sort_keys=True))


if __name__ == "__main__":
    main()
