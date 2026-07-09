"""Credential resolution for the public :class:`~onepin._client.OnepinClient`.

Hand-written; preserved across ``fern generate`` via ``.fernignore`` and re-exported from the
package ``__init__`` via ``fern/generators.yml`` ``additional_init_exports``.

Reuses the exact same priority chain the CLI uses (:mod:`onepin._cli.auth.resolver`):

  1. an explicit ``api_key`` argument
  2. the ``ONEPIN_API_KEY`` environment variable
  3. ``~/.onepin/credentials`` (written by ``onepin login``)

so ``onepin login`` authenticates the CLI and the SDK in one step. The CLI auth modules depend
only on the standard library, so importing this never pulls ``click``/``typer`` into
``import onepin``. ``base_url`` is resolved independently (explicit arg > ``ONEPIN_BASE_URL`` >
file), matching the CLI.
"""

from __future__ import annotations

import typing

from onepin._cli.auth.resolver import ResolvedCredentials, resolve_credentials


class OnepinAuthError(RuntimeError):
    """No Onepin API key could be resolved for :class:`~onepin._client.OnepinClient`."""


def resolve_credentials_for_client(
    api_key: typing.Optional[str] = None,
    base_url: typing.Optional[str] = None,
) -> ResolvedCredentials:
    """Resolve an API key (and base URL) for constructing a client.

    Args:
        api_key: An explicit key; wins over the environment and the credentials file.
        base_url: An explicit base URL; wins over ``ONEPIN_BASE_URL`` and the file.

    Returns:
        The resolved credentials, guaranteed to carry a non-empty ``api_key``.

    Raises:
        OnepinAuthError: If no key is found in the argument, the environment, or the file.
    """
    creds = resolve_credentials(flag_api_key=api_key, flag_base_url=base_url)
    if not creds.api_key:
        raise OnepinAuthError(
            "No Onepin API key found. Pass OnepinClient(api_key=...), set ONEPIN_API_KEY, "
            "or run `onepin login`."
        )
    return creds
