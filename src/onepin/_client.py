"""Public ``OnepinClient`` / ``AsyncOnepinClient`` — credential-resolving, version-gated.

Hand-written; preserved across ``fern generate`` via ``.fernignore`` and re-exported from the
package ``__init__`` via ``fern/generators.yml`` ``additional_init_exports``::

    from onepin import OnepinClient

    client = OnepinClient()                       # key from `onepin login`, then ONEPIN_API_KEY
    client = OnepinClient(api_key="op_live_...")   # explicit
    client = OnepinClient(base_url="https://api.onepin.ai", timeout=120.0)

These subclass the Fern-generated clients, so every resource (``client.workflows``,
``client.runs``, ...) is inherited unchanged. Two things are added on top:

- **Credential auto-resolution** — the API key comes from the ``api_key`` argument, then
  ``ONEPIN_API_KEY``, then ``~/.onepin/credentials`` (see :mod:`onepin._auth_resolve`), and is
  passed to the generated client as the bearer ``token``.
- **The version gate** — the same httpx response hook :func:`onepin.make_client` installs, so an
  out-of-date SDK raises :class:`~onepin._version_gate.OnePinUpgradeRequiredError`.
"""

from __future__ import annotations

import typing

import httpx

from onepin._auth_resolve import OnepinAuthError as OnepinAuthError  # re-export
from onepin._auth_resolve import resolve_credentials_for_client
from onepin._version_gate import _async_response_hook, _response_hook, _user_agent
from onepin.client import AsyncOnePinClient as _AsyncGeneratedClient
from onepin.client import OnePinClient as _GeneratedClient

_DEFAULT_TIMEOUT = 60


class OnepinClient(_GeneratedClient):
    """The Onepin client. Resolves credentials, then behaves like the generated client."""

    def __init__(
        self,
        *,
        api_key: typing.Optional[str] = None,
        base_url: typing.Optional[str] = None,
        timeout: float = _DEFAULT_TIMEOUT,
        headers: typing.Optional[typing.Dict[str, str]] = None,
        httpx_client: typing.Optional[httpx.Client] = None,
        **kwargs: typing.Any,
    ) -> None:
        creds = resolve_credentials_for_client(api_key=api_key, base_url=base_url)
        merged_headers = dict(headers or {})
        merged_headers.setdefault("User-Agent", _user_agent())
        if httpx_client is None:
            httpx_client = httpx.Client(
                timeout=timeout,
                follow_redirects=True,
                event_hooks={"response": [_response_hook]},
            )
        super().__init__(
            base_url=creds.base_url,
            token=creds.api_key,
            headers=merged_headers,
            httpx_client=httpx_client,
            **kwargs,
        )


class AsyncOnepinClient(_AsyncGeneratedClient):
    """The async Onepin client. Same resolution as :class:`OnepinClient`; ``await`` its methods."""

    def __init__(
        self,
        *,
        api_key: typing.Optional[str] = None,
        base_url: typing.Optional[str] = None,
        timeout: float = _DEFAULT_TIMEOUT,
        headers: typing.Optional[typing.Dict[str, str]] = None,
        httpx_client: typing.Optional[httpx.AsyncClient] = None,
        **kwargs: typing.Any,
    ) -> None:
        creds = resolve_credentials_for_client(api_key=api_key, base_url=base_url)
        merged_headers = dict(headers or {})
        merged_headers.setdefault("User-Agent", _user_agent())
        if httpx_client is None:
            httpx_client = httpx.AsyncClient(
                timeout=timeout,
                follow_redirects=True,
                event_hooks={"response": [_async_response_hook]},
            )
        super().__init__(
            base_url=creds.base_url,
            token=creds.api_key,
            headers=merged_headers,
            httpx_client=httpx_client,
            **kwargs,
        )


__all__ = ["AsyncOnepinClient", "OnepinAuthError", "OnepinClient"]
