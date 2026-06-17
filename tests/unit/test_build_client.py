"""Unit tests for build_client (onepin._cli._ctx)."""

from __future__ import annotations

import pytest

from onepin._cli._ctx import build_client
from onepin._cli._http import OnePinAuthError
from onepin._cli.auth.resolver import ResolvedCredentials


def test_requires_api_key() -> None:
    """No key → raise rather than build an unauthenticated client."""
    creds = ResolvedCredentials(api_key=None, base_url=None, source="default")
    with pytest.raises(OnePinAuthError):
        build_client(creds)


def test_sends_bearer_token() -> None:
    client = build_client(ResolvedCredentials(api_key="op_live_abc", base_url=None, source="flag"))
    assert client._client_wrapper.get_headers()["Authorization"] == "Bearer op_live_abc"


def test_defaults_to_prod() -> None:
    client = build_client(ResolvedCredentials(api_key="op_live_abc", base_url=None, source="flag"))
    assert client._client_wrapper.get_base_url() == "https://api.onepin.ai"


def test_honors_custom_base_url() -> None:
    """--base-url must reach the client, not be silently dropped to PROD.

    Asserts on ``client._client_wrapper`` (Fern-generated internals) — the lightest way
    to verify wiring without a live request.
    """
    client = build_client(
        ResolvedCredentials(api_key="op_live_abc", base_url="https://dev-api.onepin.ai", source="flag")
    )
    assert client._client_wrapper.get_base_url() == "https://dev-api.onepin.ai"


def test_rejects_non_http_base_url() -> None:
    """A file://-style base URL must be rejected, never receive the token."""
    creds = ResolvedCredentials(api_key="op_live_abc", base_url="file:///etc/passwd", source="flag")
    with pytest.raises(OnePinAuthError):
        build_client(creds)
