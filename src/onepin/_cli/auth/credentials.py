"""Read/write ~/.onepin/credentials TOML file with mode 0600.

Uses ``tomllib`` (stdlib 3.11+) or ``tomli`` (backport for 3.10).
Writes are hand-formatted TOML -- avoids the ``tomli_w`` dependency.

Malformed TOML on read raises SystemExit(1) -- fail fast, no silent skip.
"""
from __future__ import annotations

import os
import stat
import sys
from pathlib import Path
from typing import Any, Dict, Optional


def _credentials_path() -> Path:
    return Path.home() / ".onepin" / "credentials"


def _load_toml(path: Path) -> Dict[str, Any]:
    """Parse TOML from path. Hard-fails on parse error."""
    try:
        if sys.version_info >= (3, 11):
            import tomllib

            with open(path, "rb") as f:
                return tomllib.load(f)
        else:
            import tomli  # type: ignore[import-not-found]

            with open(path, "rb") as f:
                return tomli.load(f)
    except Exception as exc:  # noqa: BLE001
        sys.stderr.write(f"[ERROR] Malformed credentials file at {path}: {exc}\n")
        sys.exit(1)


def read_credentials() -> Optional[Dict[str, Any]]:
    """Read credentials file. Returns None if file does not exist.

    Raises:
        SystemExit(1): If the file exists but cannot be parsed as TOML.
    """
    path = _credentials_path()
    if not path.exists():
        return None
    return _load_toml(path)


def write_credentials(api_key: str, base_url: str, profile: str = "default") -> Path:
    """Write credentials to ~/.onepin/credentials with mode 0600.

    Creates ~/.onepin/ with mode 0700 if it does not exist.

    Args:
        api_key: The API key to store.
        base_url: The base URL to store.
        profile: Profile name (default: "default").

    Returns:
        Path to the written credentials file.
    """
    path = _credentials_path()
    parent = path.parent

    # Create parent directory with mode 0700
    parent.mkdir(mode=0o700, parents=True, exist_ok=True)

    content = f'[{profile}]\napi_key = "{api_key}"\nbase_url = "{base_url}"\n'

    # Write atomically: write to temp file, then rename
    tmp_path = path.with_suffix(".tmp")
    try:
        tmp_path.write_text(content, encoding="utf-8")
        if os.name != "nt":
            os.chmod(tmp_path, stat.S_IRUSR | stat.S_IWUSR)  # 0600
        tmp_path.replace(path)
    except Exception:
        tmp_path.unlink(missing_ok=True)
        raise

    return path


def delete_credentials() -> bool:
    """Delete credentials file. Returns True if deleted, False if not found."""
    path = _credentials_path()
    if path.exists():
        path.unlink()
        return True
    return False
