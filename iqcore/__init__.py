"""Shared scientific engine for the iQuant4 ecosystem.

The public subpackages are loaded lazily so that ``import iqcore`` remains
lightweight while users can still write, for example, ``iqcore.states``.
"""

from __future__ import annotations

from importlib import import_module
from types import ModuleType

from ._version import __version__

_PUBLIC_SUBMODULES = {
    "channels",
    "measurements",
    "metrics",
    "operators",
    "optics",
    "phase_space",
    "states",
    "tomography",
    "visualization",
}


def __getattr__(name: str) -> ModuleType:
    if name in _PUBLIC_SUBMODULES:
        module = import_module(f"{__name__}.{name}")
        globals()[name] = module
        return module
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def __dir__() -> list[str]:
    return sorted(set(globals()) | _PUBLIC_SUBMODULES)


__all__ = ["__version__", *_PUBLIC_SUBMODULES]
