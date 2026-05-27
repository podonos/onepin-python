"""Build OnePinClient from resolved credentials.

Pending Fern SDK regen -- raises NotImplementedError until client.py exists.
"""

from __future__ import annotations

from typing import Any

from onepin._cli.auth.resolver import ResolvedCredentials


def build_client(creds: ResolvedCredentials) -> Any:
    """Build and return an OnePinClient from resolved credentials.

    Args:
        creds: Resolved credentials from the priority chain.

    Returns:
        OnePinClient instance.

    Raises:
        NotImplementedError: Until the first Fern SDK regen lands.
    """
    raise NotImplementedError(
        "OnePinClient is not yet available -- Fern SDK regen has not run yet. "
        "See podonos/onepin-sdks for the Fern configuration."
    )
