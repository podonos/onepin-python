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


def _parse_error_envelope(body: object) -> Dict[str, Any]:
    """Extract ``{code, message, request_id}`` from an API error body.

    Shared by the raw-httpx auth path (this module) and the SDK error mapper
    (``_ctx.api_errors``). Handles the three shapes an error body can take:

    - ``dict``: a JSON envelope ``{"error": {"code", "message"}, "meta": {"request_id"}}``
      (also tolerates a flat ``{"code", "message", "detail"}`` shape).
    - ``str``: a raw JSON string (parsed) or an opaque message (used as ``message``).
    - ``None``: nothing extractable.

    Returns:
        A dict with any of ``code`` / ``message`` / ``request_id`` that could be found.
        Missing fields are simply absent. Never raises.
    """
    import json

    if body is None:
        return {}
    if isinstance(body, str):
        text = body.strip()
        if not text:
            return {}
        try:
            parsed = json.loads(text)
        except (ValueError, TypeError):
            return {"message": body}
        if isinstance(parsed, dict):
            return _parse_error_envelope(parsed)
        return {"message": body}
    if not isinstance(body, dict):
        return {}

    result: Dict[str, Any] = {}
    meta = body.get("meta")
    if isinstance(meta, dict) and meta.get("request_id"):
        result["request_id"] = meta["request_id"]
    error_obj = body.get("error")
    if isinstance(error_obj, dict):
        if error_obj.get("code"):
            result["code"] = error_obj["code"]
        if error_obj.get("message"):
            result["message"] = error_obj["message"]
    # Flat fallbacks (some endpoints return code/message/detail at the top level).
    if "code" not in result and body.get("code"):
        result["code"] = body["code"]
    if "message" not in result:
        if body.get("message"):
            result["message"] = body["message"]
        elif body.get("detail"):
            detail = body["detail"]
            result["message"] = detail if isinstance(detail, str) else json.dumps(detail)
    return result


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
            parsed = _parse_error_envelope(response.json())
        except Exception:  # noqa: BLE001
            parsed = {}
        request_id = parsed.get("request_id", request_id)
        error_code = parsed.get("code", error_code)
        error_message = parsed.get("message", error_message)

        if response.status_code == 426:
            # Server-enforced SDK floor. The raw auth path bypasses the SDK's api_errors()
            # mapper, so surface the same UPGRADE_REQUIRED message + copy-paste command here.
            from onepin._version_gate import format_upgrade_message, required_version_from

            required = required_version_from(dict(response.headers))
            if not required:
                try:
                    err = response.json().get("error")
                    raw = err.get("required_version") or err.get("minimum_version") if isinstance(err, dict) else None
                    required = raw.strip() if isinstance(raw, str) and raw.strip() else None
                except Exception:  # noqa: BLE001  # pragma: no cover - defensive 426 body-parse guard
                    required = None
            raise OnePinHTTPError(
                format_upgrade_message(required),
                status_code=426,
                error_code="UPGRADE_REQUIRED",
                request_id=request_id,
                response_body=body_text,
            )

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
