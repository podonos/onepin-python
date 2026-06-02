"""Secret-redaction tests for provider-keys (defensive masking, no --reveal flag)."""

from __future__ import annotations

import datetime as dt

import pytest
from typer.testing import CliRunner

from onepin._cli import _dispatch
from onepin._cli.main import app

runner = CliRunner()
NOW = dt.datetime(2025, 1, 1, tzinfo=dt.timezone.utc)
SECRET = "sk-supersecret-7890"


def _meta():
    from onepin.types.meta import Meta

    return Meta(request_id="r1", timestamp=NOW)


class _ProviderKeysClient:
    """Returns an item carrying a (hypothetical) secret-bearing field to prove masking."""

    captured_request = None

    class provider_keys:  # noqa: N801
        @staticmethod
        def put_provider_key(provider, *, request, **kw):
            _ProviderKeysClient.captured_request = request
            from onepin.types import ApiResponseProviderKeyItemOut, ProviderKeyItemOut

            item = ProviderKeyItemOut(
                provider=provider,
                credentials_schema={},
                configured=True,
                is_valid=True,
                validated_at=NOW,
                key_preview="****7890",
                status="valid",
            )
            return ApiResponseProviderKeyItemOut(data=item, meta=_meta())

        @staticmethod
        def list_provider_keys(**kw):
            from onepin.types import ApiResponseProviderKeysManifestOut, ProviderKeyItemOut, ProviderKeysManifestOut

            item = ProviderKeyItemOut(
                provider="elevenlabs",
                credentials_schema={"api_key": SECRET},
                configured=True,
                is_valid=True,
                validated_at=NOW,
                key_preview="****7890",
                status="valid",
            )
            return ApiResponseProviderKeysManifestOut(data=ProviderKeysManifestOut(providers=[item]), meta=_meta())


@pytest.fixture
def patch(monkeypatch: pytest.MonkeyPatch) -> _ProviderKeysClient:
    client = _ProviderKeysClient()
    monkeypatch.setattr(_dispatch, "get_client", lambda: client)
    return client


def _invoke(argv: list[str]):
    return runner.invoke(app, ["--api-key", "op_live_x", *argv])


class TestRedaction:
    def test_put_does_not_echo_input_key(self, patch, tmp_home) -> None:
        result = _invoke(["provider-keys", "put", "elevenlabs", "--key", SECRET, "--json"])
        assert result.exit_code == 0, result.output
        assert SECRET not in result.output
        # The secret still reached the SDK request body (just never printed).
        assert patch.captured_request == {"api_key": SECRET}

    def test_list_masks_secret_field(self, patch, tmp_home) -> None:
        """Defensive redaction: credentials_schema.api_key is masked by default.

        The server currently returns only ``key_preview`` (already masked), so this
        redaction is forward-compat protection against future API changes.
        """
        result = _invoke(["provider-keys", "list", "--json"])
        assert result.exit_code == 0, result.output
        assert SECRET not in result.output
        assert "****7890" in result.output

    def test_no_reveal_flag_exists(self, tmp_home) -> None:
        """--reveal was removed; passing it is a usage error."""
        result = _invoke(["provider-keys", "list", "--reveal", "--json"])
        assert result.exit_code == 2  # Typer usage error
