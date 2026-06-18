"""Client-side SDK version gate (hand-written; preserved across ``fern generate`` via ``.fernignore``).

The OnePin API advertises the minimum SDK version it still accepts via the
``X-OnePin-Required-Version`` response header (and enforces it with HTTP 426). This module reads
that header off every response and stops the caller when the installed ``onepin`` package is
older than the floor.

It is intentionally free of any CLI dependency so the generated SDK can re-export
:func:`make_client` (see ``fern/generators.yml`` ``additional_init_exports``) and programmatic
users get the same gate:

    import onepin

    client = onepin.make_client(token="...")   # version-gated
    client.workflows.list()                     # raises OnePinUpgradeRequiredError if too old

A bare ``OnePinClient(token=...)`` is not hooked, but still hits the server-side 426 (which the
generated client surfaces as ``ApiError``). The "recommended" (soft) upgrade nudge lives in the
CLI/agent skill, not here -- this module is only the hard ``required`` floor.
"""

from __future__ import annotations

import typing
from importlib.metadata import PackageNotFoundError
from importlib.metadata import version as _pkg_version

if typing.TYPE_CHECKING:  # pragma: no cover - type-only imports
    import httpx

    from onepin.client import AsyncOnePinClient, OnePinClient

#: Response header the API uses to advertise the minimum acceptable SDK version.
REQUIRED_VERSION_HEADER = "X-OnePin-Required-Version"

_BASE_UPGRADE_COMMAND = "pip install --upgrade onepin"


def installed_version() -> str:
    """The installed ``onepin`` package version (``0.0.0+local`` for an unbuilt editable tree)."""
    try:
        return _pkg_version("onepin")
    except PackageNotFoundError:
        return "0.0.0+local"


def _is_valid_version(value: typing.Optional[str]) -> bool:
    """True if ``value`` is a parseable PEP 440 version.

    Server-supplied required-version values are interpolated into a copy-paste ``pip`` command,
    so they MUST be validated first -- a value like ``0.5.0' --extra-index-url https://evil #``
    (e.g. from a rogue ``--base-url``) must never become extra shell arguments.
    """
    if not value:
        return False
    try:
        from packaging.version import InvalidVersion, Version
    except ModuleNotFoundError:  # tuple-fallback world: accept only digits + dots
        import re

        return bool(re.match(r"^\d+(\.\d+)*$", value))
    try:
        Version(value)
    except InvalidVersion:
        return False
    return True


def upgrade_command(required: typing.Optional[str] = None) -> str:
    """Copy-paste command that upgrades the SDK -- pinned to the floor only if it's a valid version."""
    if _is_valid_version(required):
        return f"pip install --upgrade 'onepin>={required}'"
    return _BASE_UPGRADE_COMMAND


def format_upgrade_message(required: typing.Optional[str], current: typing.Optional[str] = None) -> str:
    """The single, shared 'you must upgrade' sentence used by every surface (CLI, SDK, auth path).

    An unparseable/absent ``required`` degrades to the generic, unpinned message so a malformed or
    hostile server value is never echoed into the suggested command.
    """
    cur = current or installed_version()
    if _is_valid_version(required):
        return f"onepin {cur} is below the required minimum {required}. Upgrade: {upgrade_command(required)}"
    return f"onepin {cur} is no longer supported by the API. Upgrade: {upgrade_command()}"


class OnePinUpgradeRequiredError(Exception):
    """Raised when the installed SDK is older than the API's required floor.

    Carries the structured facts (``required``, ``current``, ``upgrade_command``) so a caller can
    render its own message; ``str(exc)`` is a complete, copy-paste-ready sentence.
    """

    def __init__(self, *, required: str, current: typing.Optional[str] = None) -> None:
        self.required = required
        self.current = current or installed_version()
        self.upgrade_command = upgrade_command(required)
        super().__init__(format_upgrade_message(required, self.current))


def required_version_from(headers: typing.Optional[typing.Mapping[str, str]]) -> typing.Optional[str]:
    """Extract the required-version header value, case-insensitively (httpx lowercases keys)."""
    if not headers:
        return None
    target = REQUIRED_VERSION_HEADER.lower()
    for key, value in headers.items():
        if key.lower() == target:
            return value.strip() or None
    return None


def is_older(current: str, required: str) -> bool:
    """True if ``current`` < ``required``. Unparseable versions are treated as not-older (no-op)."""
    try:
        from packaging.version import InvalidVersion, Version
    except ModuleNotFoundError:  # packaging not installed -> tuple fallback
        return _tuple_older(current, required)
    try:
        return Version(current) < Version(required)
    except InvalidVersion:
        return False


def _tuple_older(current: str, required: str) -> bool:
    """Best-effort numeric-dotted compare used only when ``packaging`` is unavailable."""

    def parse(value: str) -> tuple[int, ...]:
        head = value.split("+", 1)[0].split("-", 1)[0]
        parts: list[int] = []
        for piece in head.split("."):
            if not piece.isdigit():
                break
            parts.append(int(piece))
        return tuple(parts)

    try:
        return parse(current) < parse(required)
    except Exception:  # noqa: BLE001 - never let a compare crash a request
        return False


def check_required(
    headers: typing.Optional[typing.Mapping[str, str]],
    *,
    current: typing.Optional[str] = None,
) -> None:
    """Raise :class:`OnePinUpgradeRequiredError` if ``headers`` advertise a floor above the install.

    Missing/blank/unparseable header -> no-op, so the gate stays inert until the API emits it.
    """
    required = required_version_from(headers)
    if not required:
        return
    installed = current or installed_version()
    if is_older(installed, required):
        raise OnePinUpgradeRequiredError(required=required, current=installed)


def _response_hook(response: "httpx.Response") -> None:
    """httpx response event hook -- reads only headers, so it never consumes the body."""
    check_required(response.headers)


async def _async_response_hook(response: "httpx.Response") -> None:
    check_required(response.headers)


def _user_agent() -> str:
    return f"onepin/{installed_version()}"


def make_client(**kwargs: typing.Any) -> OnePinClient:
    """Build a version-gated :class:`~onepin.client.OnePinClient`.

    Drop-in for ``OnePinClient(...)``: injects an httpx client whose response hook enforces the
    server's required-version floor and corrects the ``User-Agent`` to the true installed version
    (the generated default is baked at codegen time and can drift). A caller-supplied
    ``httpx_client`` is respected (assumed already configured); ``headers`` are merged.
    """
    import httpx

    from onepin.client import OnePinClient

    headers = dict(kwargs.pop("headers", None) or {})
    headers.setdefault("User-Agent", _user_agent())
    if "httpx_client" not in kwargs:
        kwargs["httpx_client"] = httpx.Client(
            timeout=kwargs.pop("timeout", 60),
            follow_redirects=kwargs.pop("follow_redirects", True),
            event_hooks={"response": [_response_hook]},
        )
    return OnePinClient(headers=headers, **kwargs)


def make_async_client(**kwargs: typing.Any) -> AsyncOnePinClient:
    """Async counterpart of :func:`make_client`."""
    import httpx

    from onepin.client import AsyncOnePinClient

    headers = dict(kwargs.pop("headers", None) or {})
    headers.setdefault("User-Agent", _user_agent())
    if "httpx_client" not in kwargs:
        kwargs["httpx_client"] = httpx.AsyncClient(
            timeout=kwargs.pop("timeout", 60),
            follow_redirects=kwargs.pop("follow_redirects", True),
            event_hooks={"response": [_async_response_hook]},
        )
    return AsyncOnePinClient(headers=headers, **kwargs)
