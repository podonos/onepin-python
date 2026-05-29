"""Build a configured OnePinClient from resolved credentials."""

from __future__ import annotations

from urllib.parse import urlparse

from onepin._cli._http import OnePinAuthError
from onepin._cli.auth.resolver import ResolvedCredentials
from onepin.client import OnePinClient
from onepin.environment import OnePinClientEnvironment


def build_client(creds: ResolvedCredentials) -> OnePinClient:
    """Build an OnePinClient from resolved credentials.

    A custom base URL (e.g. ``--base-url`` for dev/staging) is honored by building a
    matching environment; production is the default. An API key is required — this
    raises rather than sending an empty ``Authorization: Bearer`` header.

    Args:
        creds: Resolved credentials from the priority chain.

    Returns:
        A configured OnePinClient.

    Raises:
        OnePinAuthError: If no API key is available, or the base URL is not http(s)
            (guards against sending the bearer token to a ``file://``/``ftp://`` host).
    """
    if not creds.api_key:
        raise OnePinAuthError(
            "Not logged in. Run `onepin login`, set ONEPIN_API_KEY, or pass --api-key.",
            error_code="NOT_AUTHENTICATED",
        )
    if creds.base_url:
        if urlparse(creds.base_url).scheme not in ("http", "https"):
            raise OnePinAuthError(
                f"Invalid base URL {creds.base_url!r}: only http and https are supported.",
                error_code="INVALID_BASE_URL",
            )
        environment = OnePinClientEnvironment(api=creds.base_url)
    else:
        environment = OnePinClientEnvironment.PROD
    return OnePinClient(
        environment=environment,
        headers={"Authorization": f"Bearer {creds.api_key}"},
    )
