"""Command-line interface for the iQuant4 developer-alpha showcase."""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence
from pathlib import Path

from .dashboard import build_showcase_dashboard, open_showcase_dashboard
from .lossy_cat import run_lossy_cat_showcase
from .receiver_family import run_receiver_family_showcase
from .runner import run_alpha_showcase
from .tomography import run_sign_free_tomography_showcase


def build_argument_parser() -> argparse.ArgumentParser:
    """Build the showcase command-line parser."""
    parser = argparse.ArgumentParser(
        prog="iq4comm showcase",
        description=(
            "Generate reproducible iQuant4 developer-alpha reports, figures, "
            "and an offline HTML dashboard."
        ),
    )
    parser.add_argument(
        "component",
        nargs="?",
        choices=("all", "receiver-family", "lossy-cat", "tomography", "dashboard"),
        default="all",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("showcase_output"),
    )
    parser.add_argument(
        "--skip-tomography",
        action="store_true",
        help="Skip the optional CVXPY tomography showcase when running all.",
    )
    parser.add_argument(
        "--require-cvxpy",
        action="store_true",
        help="Fail instead of recording a skipped tomography artifact.",
    )
    parser.add_argument(
        "--skip-dashboard",
        action="store_true",
        help="Do not build the offline HTML dashboard when running all.",
    )
    parser.add_argument(
        "--open",
        action="store_true",
        help="Open the generated dashboard in the system default browser.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Run one showcase component or the complete alpha showcase."""
    parser = build_argument_parser()
    args = parser.parse_args(argv)
    output_directory = args.output_dir.resolve()

    if args.open and args.component not in {"all", "dashboard"}:
        parser.error("--open is available only for all or dashboard.")

    if args.component == "receiver-family":
        result = run_receiver_family_showcase(output_directory)
        print(result.report_path.read_text(encoding="utf-8"))
        print(f"Artifacts: {result.output_directory}")
        return 0

    if args.component == "lossy-cat":
        result = run_lossy_cat_showcase(output_directory)
        print("Loss-degraded cat-state showcase completed.")
        print(f"Artifacts: {result.output_directory}")
        return 0

    if args.component == "tomography":
        result = run_sign_free_tomography_showcase(
            output_directory,
            require_cvxpy=args.require_cvxpy,
        )
        print(f"Sign-free tomography status: {result.status}")
        if result.fidelity is not None:
            print(f"Fidelity: {result.fidelity:.6f}")
        print(f"Artifacts: {result.output_directory}")
        return 0

    if args.component == "dashboard":
        try:
            result = build_showcase_dashboard(
                output_directory,
                open_browser=args.open,
            )
        except FileNotFoundError as error:
            print(str(error), file=sys.stderr)
            return 2
        print(f"Dashboard: {result.html_path}")
        print(f"Standalone dashboard: {result.standalone_html_path}")
        return 0

    manifest = run_alpha_showcase(
        output_directory,
        include_tomography=not args.skip_tomography,
        require_cvxpy=args.require_cvxpy,
        include_dashboard=not args.skip_dashboard,
    )
    print("iQuant4 developer-alpha showcase completed.")
    print(f"Manifest: {manifest['manifest_path']}")
    if "dashboard_path" in manifest:
        print(f"Dashboard: {manifest['dashboard_path']}")
        print(f"Standalone dashboard: {manifest['standalone_dashboard_path']}")
        if args.open:
            open_showcase_dashboard(manifest["dashboard_path"])
    return 0


__all__ = ["build_argument_parser", "main"]
