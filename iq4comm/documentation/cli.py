"""Command-line interface for the installed iQuant4 documentation portal."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

from .portal import build_documentation_portal, open_documentation_portal


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="iq4comm docs",
        description="Build or open the offline iQuant4 documentation portal.",
    )
    subparsers = parser.add_subparsers(dest="command")

    build = subparsers.add_parser("build", help="Build the offline portal.")
    build.add_argument(
        "--output-dir",
        type=Path,
        default=Path("documentation_output"),
    )
    build.add_argument("--open", action="store_true")

    open_parser = subparsers.add_parser(
        "open", help="Open a previously built portal."
    )
    open_parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("documentation_output"),
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    arguments = _parser().parse_args(argv)
    if arguments.command == "build":
        result = build_documentation_portal(
            arguments.output_dir,
            open_browser=arguments.open,
        )
        print("iQuant4 documentation portal built")
        print(f"Pages       : {result.page_count}")
        print(f"API symbols : {result.symbol_count}")
        print(f"Index       : {result.index_path}")
        return 0
    if arguments.command == "open":
        open_documentation_portal(arguments.output_dir)
        return 0
    _parser().print_help(sys.stderr)
    return 2


__all__ = ["main"]
