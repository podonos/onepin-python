"""OnePin CLI -- hand-rolled Typer CLI atop the Fern-generated SDK."""

from __future__ import annotations

from importlib.metadata import PackageNotFoundError
from importlib.metadata import version as _pkg_version

try:
    __version__ = _pkg_version("onepin")
except PackageNotFoundError:  # editable install pre-build
    __version__ = "0.0.0+local"

__all__ = ["__version__"]
