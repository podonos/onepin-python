"""Credential resolution: flag > env > file > None.

Priority chain (highest wins):
  1. Explicit --api-key flag (passed as ``flag_api_key``)
  2. ``ONEPIN_API_KEY`` environment variable
  3. ``~/.onepin/credentials`` TOML file, ``[default]`` profile
  4. None (caller decides whether to abort)

Malformed TOML file raises hard error -- no silent fallback per project policy.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Literal, Optional

from onepin._cli.auth.credentials import read_credentials


@dataclass
class ResolvedCredentials:
    api_key: Optional[str]
    base_url: Optional[str]
    source: Literal["flag", "env", "file", "default"]


def _resolve_base_url(
    flag_base_url: Optional[str],
    file_base_url: Optional[str] = None,
) -> Optional[str]:
    """Resolve base_url INDEPENDENTLY of where api_key came from.

    Precedence: flag_base_url > ONEPIN_BASE_URL env > file [default].base_url > None.
    This ensures ``ONEPIN_BASE_URL=https://staging onepin --api-key op_live_x ...``
    targets staging (not production), regardless of the api_key source.
    """
    if flag_base_url is not None:
        return flag_base_url
    env_url = os.environ.get("ONEPIN_BASE_URL")
    if env_url:
        return env_url
    if file_base_url:
        return file_base_url
    return None


def resolve_credentials(
    flag_api_key: Optional[str] = None,
    flag_base_url: Optional[str] = None,
) -> ResolvedCredentials:
    """Resolve credentials from the priority chain.

    api_key precedence: flag > env > file > None.
    base_url precedence (independent): flag > env > file > None.

    Args:
        flag_api_key: Value of --api-key CLI flag (None if not provided).
        flag_base_url: Value of --base-url CLI flag (None if not provided).

    Returns:
        ResolvedCredentials with source indicating where the key came from.

    Raises:
        SystemExit: If the credentials file exists but is malformed TOML.
    """
    # Read the credentials file once (may be needed for both api_key and base_url).
    file_data = read_credentials()  # raises hard on malformed TOML
    file_profile = file_data.get("default", {}) if file_data is not None else {}
    file_base_url = file_profile.get("base_url")

    # base_url resolved independently of api_key source.
    base_url = _resolve_base_url(flag_base_url, file_base_url)

    # 1. Explicit flag
    if flag_api_key is not None:
        return ResolvedCredentials(
            api_key=flag_api_key,
            base_url=base_url,
            source="flag",
        )

    # 2. Environment variable
    env_key = os.environ.get("ONEPIN_API_KEY")
    if env_key:
        return ResolvedCredentials(
            api_key=env_key,
            base_url=base_url,
            source="env",
        )

    # 3. Credentials file (~/.onepin/credentials)
    file_key = file_profile.get("api_key")
    if file_key:
        return ResolvedCredentials(
            api_key=file_key,
            base_url=base_url,
            source="file",
        )

    # 4. Nothing found
    return ResolvedCredentials(api_key=None, base_url=base_url, source="default")
