"""Shared httpx helper for CLI auth calls.

Provides a typed exception hierarchy and a single _call_whoami() function
used by login, logout, and whoami commands.

No Fern SDK dependency -- direct httpx calls only.
"""

from __future__ import annotations

import sys
from typing import Any, Dict, Optional, cast

import httpx

from onepin._cli import __version__


class OnePinHTTPError(Exception):
    """Base error for all HTTP-layer failures.

    Attributes:
        status_code: HTTP status code, or None for network-level errors.
        error_code: Machine-readable error code from the response envelope.
        message: Human-readable message.
        request_id: Request-ID from the response meta envelope, if available.
        response_body: Raw response body string, if available.
    """

    def __init__(
        self,
        message: str,
        *,
        status_code: Optional[int] = None,
        error_code: str = "HTTP_ERROR",
        request_id: Optional[str] = None,
        response_body: Optional[str] = None,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.error_code = error_code
        self.message = message
        self.request_id = request_id
        self.response_body = response_body


class OnePinAuthError(OnePinHTTPError):
    """Raised for 401 / 403 responses."""


class OnePinNetworkError(OnePinHTTPError):
    """Raised for connection / timeout failures (no status code)."""


def _user_agent() -> str:
    major = sys.version_info.major
    minor = sys.version_info.minor
    return f"onepin-python/{__version__} python/{major}.{minor}"


def _call_whoami(key: str, base_url: str, timeout: float = 10.0, *, verbose: bool = False) -> Dict[str, Any]:
    """Call GET /api/v1/auth/whoami and return the ``data`` field.

    Args:
        key: API key to authenticate with.
        base_url: Base URL of the OnePin API (no trailing slash).
        timeout: Request timeout in seconds.
        verbose: If True, log the request and response status to stderr.

    Returns:
        Parsed ``data`` dict from the response envelope.

    Raises:
        OnePinAuthError: On 401 or 403.
        OnePinNetworkError: On connection or timeout failure.
        OnePinHTTPError: On any other non-2xx response.
    """
    url = f"{base_url.rstrip('/')}/api/v1/auth/whoami"
    headers = {
        "Authorization": f"Bearer {key}",
        "User-Agent": _user_agent(),
    }
    if verbose:
        print(f"→ GET {url}", file=sys.stderr)
    try:
        with httpx.Client(timeout=timeout) as client:
            response = client.get(url, headers=headers)
    except (httpx.ConnectError, httpx.TimeoutException) as exc:
        raise OnePinNetworkError(
            f"Could not reach {base_url}. Pass --verbose for details.",
            error_code="NETWORK_ERROR",
        ) from exc

    if verbose:
        print(f"← {response.status_code} {response.reason_phrase}", file=sys.stderr)

    # Try to extract envelope fields for richer errors
    request_id: Optional[str] = None
    error_code = "HTTP_ERROR"
    error_message = response.reason_phrase or "Request failed"
    body_text = response.text

    if response.status_code != 200:
        try:
            payload = response.json()
            meta = payload.get("meta", {})
            request_id = meta.get("request_id")
            error_obj = payload.get("error", {})
            error_code = error_obj.get("code", error_code)
            error_message = error_obj.get("message", error_message)
        except Exception:  # noqa: BLE001
            pass

        if response.status_code in (401, 403):
            raise OnePinAuthError(
                error_message,
                status_code=response.status_code,
                error_code="INVALID_API_KEY",
                request_id=request_id,
                response_body=body_text,
            )

        raise OnePinHTTPError(
            error_message,
            status_code=response.status_code,
            error_code=error_code,
            request_id=request_id,
            response_body=body_text,
        )

    payload = response.json()
    return cast(Dict[str, Any], payload["data"])
