"""High-level communication analysis workflows.

The receiver-family module is loaded lazily so command-line execution through
``python -m iq4comm.analysis.receiver_family`` does not pre-import the module.
"""

from __future__ import annotations

from importlib import import_module
from typing import Any

_PUBLIC_NAMES = {
    "ReceiverFamilyConfiguration",
    "ReceiverFamilyRow",
    "compare_receiver_families",
    "format_receiver_family_report",
}


def __getattr__(name: str) -> Any:
    if name in _PUBLIC_NAMES:
        module = import_module(f"{__name__}.receiver_family")
        value = getattr(module, name)
        globals()[name] = value
        return value
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def __dir__() -> list[str]:
    return sorted(set(globals()) | _PUBLIC_NAMES)


__all__ = sorted(_PUBLIC_NAMES)
