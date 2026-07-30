"""Unified command-line interface for the iQuant4Comm developer alpha."""

from __future__ import annotations

import sys

from ._version import __version__
from .analysis.receiver_family import main as receiver_family_main
from .diagnostics import main as doctor_main
from .documentation.cli import main as documentation_main
from .portal.cli import main as portal_main
from .showcase.cli import main as showcase_main


_HELP = """\
iQuant4Comm developer-alpha command line

Usage:
  iq4comm --version
  iq4comm doctor [--json]
  iq4comm docs {build,open} [documentation options]
  iq4comm portal {build,open} [portal options]
  iq4comm receiver-family [receiver-family options]
  iq4comm showcase [component] [showcase options]

Commands:
  doctor           Check installation and core scientific invariants.
  docs             Build or open the offline documentation portal.
  portal           Build or open the static public-preview portal.
  receiver-family  Optimize and compare PNR, homodyne, and heterodyne families.
  showcase         Generate flagship reports, figures, and the HTML dashboard.

Use ``iq4comm receiver-family --help`` or ``iq4comm showcase --help`` for options.

Quick documentation portal:
  iq4comm docs build --output-dir documentation_output --open

Quick public preview:
  iq4comm portal build --output-dir public_preview --open

Quick dashboard:
  iq4comm showcase dashboard --output-dir showcase_output --open
"""


def main(argv: list[str] | None = None) -> int:
    """Dispatch the unified iQuant4Comm command line."""
    arguments = list(sys.argv[1:] if argv is None else argv)

    if not arguments or arguments[0] in {"-h", "--help"}:
        print(_HELP)
        return 0

    if arguments[0] in {"-V", "--version"}:
        print(__version__)
        return 0

    command, command_arguments = arguments[0], arguments[1:]
    if command == "doctor":
        return doctor_main(command_arguments)
    if command == "docs":
        return documentation_main(command_arguments)
    if command == "portal":
        return portal_main(command_arguments)
    if command == "receiver-family":
        receiver_family_main(command_arguments)
        return 0
    if command == "showcase":
        return showcase_main(command_arguments)

    print(f"Unknown command: {command}", file=sys.stderr)
    print(_HELP, file=sys.stderr)
    return 2


__all__ = ["main"]
