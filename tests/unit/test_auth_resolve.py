"""Credential resolution + OnepinClient construction (hand-rolled, .fernignore-preserved)."""

from __future__ import annotations

import pytest

from onepin import AsyncOnepinClient, OnepinAuthError, OnepinClient
from onepin._auth_resolve import resolve_credentials_for_client


@pytest.fixture(autouse=True)
def _isolate_env(tmp_path, monkeypatch):
    """Every test starts with no env keys and an empty HOME (no real ~/.onepin/credentials)."""
    monkeypatch.delenv("ONEPIN_API_KEY", raising=False)
    monkeypatch.delenv("ONEPIN_BASE_URL", raising=False)
    monkeypatch.setenv("HOME", str(tmp_path))


def _write_credentials(tmp_path, *, api_key="op_live_file", base_url="https://file.onepin.ai"):
    cfg = tmp_path / ".onepin"
    cfg.mkdir(parents=True, exist_ok=True)
    (cfg / "credentials").write_text(f'[default]\napi_key = "{api_key}"\nbase_url = "{base_url}"\n')


def test_explicit_api_key_wins():
    creds = resolve_credentials_for_client(api_key="op_live_explicit")
    assert creds.api_key == "op_live_explicit"
    assert creds.source == "flag"


def test_env_var_used_when_no_argument(monkeypatch):
    monkeypatch.setenv("ONEPIN_API_KEY", "op_live_env")
    creds = resolve_credentials_for_client()
    assert creds.api_key == "op_live_env"
    assert creds.source == "env"


def test_explicit_argument_beats_env(monkeypatch):
    monkeypatch.setenv("ONEPIN_API_KEY", "op_live_env")
    creds = resolve_credentials_for_client(api_key="op_live_explicit")
    assert creds.api_key == "op_live_explicit"


def test_credentials_file_used_when_no_arg_or_env(tmp_path):
    _write_credentials(tmp_path)
    creds = resolve_credentials_for_client()
    assert creds.api_key == "op_live_file"
    assert creds.base_url == "https://file.onepin.ai"
    assert creds.source == "file"


def test_no_key_anywhere_raises():
    with pytest.raises(OnepinAuthError):
        resolve_credentials_for_client()


def test_base_url_argument_wins_over_file(tmp_path):
    _write_credentials(tmp_path)
    creds = resolve_credentials_for_client(base_url="https://override.onepin.ai")
    assert creds.base_url == "https://override.onepin.ai"


def test_client_constructs_with_explicit_key_offline():
    client = OnepinClient(api_key="op_live_x", base_url="https://api.onepin.ai")
    # Resource groups are inherited from the generated client; no network happens here.
    assert hasattr(client, "workflows")
    assert hasattr(client, "voices")


def test_client_without_any_key_raises():
    with pytest.raises(OnepinAuthError):
        OnepinClient()


def test_async_client_constructs_with_explicit_key_offline():
    client = AsyncOnepinClient(api_key="op_live_x")
    assert hasattr(client, "workflows")
