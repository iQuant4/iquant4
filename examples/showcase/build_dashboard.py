"""Rebuild an iQuant4 showcase dashboard from existing artifacts."""

from __future__ import annotations

from pathlib import Path

from iq4comm.showcase import build_showcase_dashboard


OUTPUT_DIRECTORY = Path("showcase_output")


def main() -> None:
    result = build_showcase_dashboard(OUTPUT_DIRECTORY)
    print(f"Dashboard: {result.html_path}")
    print(f"Standalone dashboard: {result.standalone_html_path}")


if __name__ == "__main__":
    main()
