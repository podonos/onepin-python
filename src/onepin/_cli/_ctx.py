"""Build a configured OnePinClient from resolved credentials."""

from __future__ import annotations

from urllib.parse import urlparse

from onepin._cli._http import OnePinAuthError
from onepin._cli.auth.resolver import ResolvedCredentials
from onepin.client import OnePinClient


def build_client(creds: ResolvedCredentials) -> OnePinClient:
    """Build an OnePinClient from resolved credentials.

    The API key is passed as the SDK ``token`` (sent as ``Authorization: Bearer``); a
    custom ``--base-url`` is passed straight through, and an empty one falls back to the
    default production environment. An API key is required — this raises rather than
    building an unauthenticated client.

    Args:
        creds: Resolved credentials from the priority chain.

    Returns:
        A configured OnePinClient.

    Raises:
        OnePinAuthError: If no API key is available, or the base URL is not http(s)
            (guards against sending the token to a ``file://``/``ftp://`` host).
    """
    if not creds.api_key:
        raise OnePinAuthError(
            "Not logged in. Run `onepin login`, set ONEPIN_API_KEY, or pass --api-key.",
            error_code="NOT_AUTHENTICATED",
        )
    if creds.base_url and urlparse(creds.base_url).scheme not in ("http", "https"):
        raise OnePinAuthError(
            f"Invalid base URL {creds.base_url!r}: only http and https are supported.",
            error_code="INVALID_BASE_URL",
        )
    return OnePinClient(base_url=creds.base_url, token=creds.api_key)
