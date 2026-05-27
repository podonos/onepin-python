"""Process-local CLI option state shared between root callback and commands."""

from __future__ import annotations

from typing import Any

root_options: dict[str, Any] = {}
