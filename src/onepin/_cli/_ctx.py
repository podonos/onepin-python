"""Build a configured OnePinClient from resolved credentials."""

from __future__ import annotations

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
        OnePinAuthError: If no API key is available.
    """
    if not creds.api_key:
        raise OnePinAuthError(
            "Not logged in. Run `onepin login`, set ONEPIN_API_KEY, or pass --api-key.",
            error_code="NOT_AUTHENTICATED",
        )
    environment = OnePinClientEnvironment(api=creds.base_url) if creds.base_url else OnePinClientEnvironment.PROD
    return OnePinClient(
        environment=environment,
        headers={"Authorization": f"Bearer {creds.api_key}"},
    )
