"""Build and validate the installed iQuant4 documentation portal."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from iq4comm.documentation import build_documentation_portal


def verify_installed_documentation(output_directory: str | Path) -> dict[str, int]:
    root = Path(output_directory).expanduser().resolve()
    result = build_documentation_portal(root)
    required = (
        result.index_path,
        result.iqcore_api_path,
        result.iq4comm_api_path,
        result.manifest_path,
        result.search_index_path,
        root / "style.css",
        root / "site.js",
        root / "search_index.js",
    )
    missing = [str(path) for path in required if not path.is_file()]
    if missing:
        raise RuntimeError("documentation artifacts are missing: " + ", ".join(missing))

    index = result.index_path.read_text(encoding="utf-8")
    if "Build with" not in index or "iQuant4Comm" not in index:
        raise RuntimeError("documentation landing page is missing required branding")
    if "http://" in index or "https://" in index:
        raise RuntimeError("documentation portal uses remote runtime assets")

    core = result.iqcore_api_path.read_text(encoding="utf-8")
    communications = result.iq4comm_api_path.read_text(encoding="utf-8")
    for marker in ("coherent_state", "apply_beam_splitter", "wigner_function"):
        if marker not in core:
            raise RuntimeError(f"iqcore API page is missing {marker}")
    for marker in ("FiberChannel", "ErasurePNRReceiver", "compare_receiver_families"):
        if marker not in communications:
            raise RuntimeError(f"iq4comm API page is missing {marker}")

    manifest = json.loads(result.manifest_path.read_text(encoding="utf-8"))
    search = json.loads(result.search_index_path.read_text(encoding="utf-8"))
    if not manifest.get("offline_ready"):
        raise RuntimeError("documentation manifest does not report offline readiness")
    if len(search) < 10:
        raise RuntimeError("documentation search index is incomplete")

    summary = {
        "pages": result.page_count,
        "symbols": result.symbol_count,
        "search_records": len(search),
    }
    print("installed documentation verification passed")
    for key, value in summary.items():
        print(f"{key}: {value}")
    return summary


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output_directory", type=Path)
    arguments = parser.parse_args(argv)
    verify_installed_documentation(arguments.output_directory)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
