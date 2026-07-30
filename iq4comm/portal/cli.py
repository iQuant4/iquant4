"""Command-line interface for the iQuant4 public-preview site."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

from .site import build_public_preview, open_public_preview


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="iq4comm portal",
        description="Build or open the static iQuant4 public-preview portal.",
    )
    subparsers = parser.add_subparsers(dest="command")

    build = subparsers.add_parser(
        "build", help="Build documentation, showcase, and landing pages."
    )
    build.add_argument(
        "--output-dir", type=Path, default=Path("public_preview")
    )
    build.add_argument("--skip-showcase", action="store_true")
    build.add_argument("--include-tomography", action="store_true")
    build.add_argument("--require-cvxpy", action="store_true")
    build.add_argument("--open", action="store_true")

    open_parser = subparsers.add_parser(
        "open", help="Open an existing public-preview portal."
    )
    open_parser.add_argument(
        "--output-dir", type=Path, default=Path("public_preview")
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _parser()
    arguments = parser.parse_args(argv)
    if arguments.command == "build":
        result = build_public_preview(
            arguments.output_dir,
            include_showcase=not arguments.skip_showcase,
            include_tomography=arguments.include_tomography,
            require_cvxpy=arguments.require_cvxpy,
            open_browser=arguments.open,
        )
        print("iQuant4 public preview built")
        print(f"Pages      : {result.page_count}")
        print(f"Showcase   : {result.showcase_generated}")
        print(f"Index      : {result.index_path}")
        return 0
    if arguments.command == "open":
        open_public_preview(arguments.output_dir)
        return 0
    parser.print_help(sys.stderr)
    return 2


__all__ = ["main"]
