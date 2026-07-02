"""``onepin upgrade-check`` (hidden) -- gstack-style soft upgrade notifier.

The CLI itself never nags on stderr; instead this command prints a single machine-readable
line that the ``/onepin`` agent skill reads and turns into an ``AskUserQuestion`` prompt:

    UPGRADE_AVAILABLE <current> <latest>   -- a newer release is on PyPI
    JUST_UPGRADED <old> <new>              -- a just-upgraded marker was found
    (no output)                            -- up to date / snoozed / disabled / offline

State lives under ``~/.onepin/`` (reusing the credentials home helper):
  - ``update-check``   dual-TTL cache (UP_TO_DATE 60 min; UPGRADE_AVAILABLE replays ~12 h)
  - ``update-snoozed`` ``<version> <level> <epoch>`` escalating snooze (24 h / 48 h / 7 d)
  - ``just-upgraded-from`` optional marker (``<old-version>``) cleared on read

All network and filesystem failures are swallowed -- a version check must never break tooling.
"""

from __future__ import annotations

import os
import re
import time
from pathlib import Path
from typing import Optional

import typer

from onepin._cli import __version__
from onepin._cli.auth.credentials import _home_path
from onepin._version_gate import is_older

_PYPI_URL = "https://pypi.org/pypi/onepin/json"
_FETCH_TIMEOUT = 3.0

# Cache TTLs (minutes): re-check hourly when current; replay the nag ~12 h when behind.
_TTL_UP_TO_DATE = 60
_TTL_UPGRADE_AVAILABLE = 720

# Snooze durations (seconds) by escalation level; level 3+ caps at a week.
_SNOOZE_DURATIONS = {1: 86_400, 2: 172_800}
_SNOOZE_DEFAULT = 604_800

_VERSION_RE = re.compile(r"^\d+\.\d+")


def _state_dir() -> Path:
    return _home_path() / ".onepin"


def _cache_path() -> Path:
    return _state_dir() / "update-check"


def _snooze_path() -> Path:
    return _state_dir() / "update-snoozed"


def _marker_path() -> Path:
    return _state_dir() / "just-upgraded-from"


def _disabled_path() -> Path:
    return _state_dir() / "update-check-disabled"


def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8").strip()
    except OSError:
        return ""


def _atomic_write(path: Path, content: str) -> None:
    """Write ``content`` to ``path`` atomically (tmp + os.replace); swallow OS errors.

    Avoids a torn read when two ``onepin`` processes touch the same state file at once.
    """
    import tempfile

    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        fd, tmp = tempfile.mkstemp(dir=str(path.parent), suffix=".tmp")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                handle.write(content)
            os.replace(tmp, str(path))
        except OSError:  # pragma: no cover - best-effort temp cleanup
            try:
                os.unlink(tmp)
            except OSError:
                pass
    except OSError:  # pragma: no cover - a cache write must never break the CLI
        pass


def _write_cache(line: str) -> None:
    _atomic_write(_cache_path(), line + "\n")


def _age_minutes(path: Path) -> float:
    try:
        return (time.time() - path.stat().st_mtime) / 60.0
    except OSError:  # pragma: no cover - missing/unreadable cache file
        return float("inf")


def _fetch_latest() -> Optional[str]:
    """Best-effort latest stable version from PyPI; ``None`` on any failure/offline."""
    try:
        import httpx

        response = httpx.get(_PYPI_URL, timeout=_FETCH_TIMEOUT)
        if response.status_code != 200:
            return None
        version = str(response.json().get("info", {}).get("version", "")).strip()
        return version if _VERSION_RE.match(version) else None
    except Exception:  # noqa: BLE001 - network/parse failures degrade to "no info"
        return None


def _parse_cache(line: str) -> Optional[tuple[str, str]]:
    """Parse a cache line into ``(kind, latest)``; ``None`` if unrecognized."""
    parts = line.split()
    if not parts:
        return None
    kind = parts[0]
    if kind == "UP_TO_DATE" and len(parts) >= 2:
        return ("UP_TO_DATE", parts[1])
    if kind == "UPGRADE_AVAILABLE" and len(parts) >= 3:
        return ("UPGRADE_AVAILABLE", parts[2])
    return None


def cached_latest() -> Optional[str]:
    """Latest version recorded in the cache (any freshness); ``None`` if unknown."""
    parsed = _parse_cache(_read_text(_cache_path()))
    return parsed[1] if parsed else None


def _read_fresh_latest() -> Optional[str]:
    """Latest version from the cache only if still within its per-kind TTL, else ``None``."""
    path = _cache_path()
    parsed = _parse_cache(_read_text(path))
    if parsed is None:
        return None
    kind, latest = parsed
    ttl = _TTL_UP_TO_DATE if kind == "UP_TO_DATE" else _TTL_UPGRADE_AVAILABLE
    if _age_minutes(path) > ttl:
        return None
    return latest


def _resolve_latest(current: str) -> Optional[str]:
    """Return the latest version (cache when fresh, else fetch + cache); ``None`` if unknown."""
    fresh = _read_fresh_latest()
    if fresh is not None:
        return fresh
    latest = _fetch_latest()
    if latest is None:
        # Offline / fetch error: do not cache. A failure must not masquerade as "up to date",
        # and the next run should retry rather than stay silent for the full TTL.
        return None
    if is_older(current, latest):
        _write_cache(f"UPGRADE_AVAILABLE {current} {latest}")
    else:
        _write_cache(f"UP_TO_DATE {current}")
    return latest


def _is_snoozed(latest: str) -> bool:
    parts = _read_text(_snooze_path()).split()
    if len(parts) != 3:
        return False
    version, level, epoch = parts
    if version != latest or not level.isdigit() or not epoch.isdigit():
        return False  # a new release resets the snooze
    duration = _SNOOZE_DURATIONS.get(int(level), _SNOOZE_DEFAULT)
    return time.time() < int(epoch) + duration


def _bump_snooze() -> None:
    """Escalate the snooze for the currently-cached upgrade (level +1, or 1 if new)."""
    latest = cached_latest()
    parsed = _parse_cache(_read_text(_cache_path()))
    if not latest or parsed is None or parsed[0] != "UPGRADE_AVAILABLE":
        return
    existing = _read_text(_snooze_path()).split()
    level = 1
    if len(existing) == 3 and existing[0] == latest and existing[1].isdigit():
        level = int(existing[1]) + 1
    _atomic_write(_snooze_path(), f"{latest} {level} {int(time.time())}\n")


def _consume_marker(current: str) -> bool:
    """If a just-upgraded marker exists, emit ``JUST_UPGRADED`` and return True."""
    marker = _marker_path()
    old = _read_text(marker)
    if not old:
        return False
    try:
        marker.unlink()
    except OSError:  # pragma: no cover - best-effort marker cleanup
        pass
    try:
        _snooze_path().unlink(missing_ok=True)
    except OSError:  # pragma: no cover - best-effort snooze cleanup
        pass
    _write_cache(f"UP_TO_DATE {current}")
    if old != current:
        typer.echo(f"JUST_UPGRADED {old} {current}")
    return True


def upgrade_check(
    force: bool = typer.Option(False, "--force", help="Bypass the cache and re-check now."),
    snooze: bool = typer.Option(False, "--snooze", help="Snooze the current upgrade prompt (escalating)."),
    disable: bool = typer.Option(
        False, "--disable", help="Stop all future upgrade checks (rm ~/.onepin/update-check-disabled to re-enable)."
    ),
    mark_upgrading: bool = typer.Option(
        False, "--mark-upgrading", help="Record the current version before upgrading so the next run can confirm it."
    ),
) -> None:
    """Print a one-line upgrade signal for the agent skill (hidden; not for direct use)."""
    if mark_upgrading:
        _atomic_write(_marker_path(), f"{__version__}\n")
        return
    if disable:
        _atomic_write(_disabled_path(), "1\n")
        return
    if os.environ.get("ONEPIN_NO_UPDATE_CHECK") or _disabled_path().exists():
        return

    current = __version__

    if snooze:
        _bump_snooze()
        return

    if force:
        _cache_path().unlink(missing_ok=True)

    if _consume_marker(current):
        return

    latest = _resolve_latest(current)
    if latest and is_older(current, latest) and not _is_snoozed(latest):
        typer.echo(f"UPGRADE_AVAILABLE {current} {latest}")
