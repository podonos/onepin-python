"""Unit tests for the gstack-style soft upgrade notifier (`onepin upgrade-check`)."""

from __future__ import annotations

import httpx
import pytest
import respx
from typer.testing import CliRunner

from onepin._cli import _update_check as uc
from onepin._cli.main import app

runner = CliRunner()


@pytest.fixture(autouse=True)
def _fixed_version(monkeypatch: pytest.MonkeyPatch) -> None:
    """Pin the "installed" version so comparisons are deterministic (real one is VCS-derived)."""
    monkeypatch.setattr(uc, "__version__", "0.6.0")


def _seed_cache(line: str) -> None:
    path = uc._cache_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(line + "\n", encoding="utf-8")


class TestUpgradeAvailable:
    def test_fetch_prints_and_caches(self, tmp_home, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(uc, "_fetch_latest", lambda: "0.9.0")
        result = runner.invoke(app, ["upgrade-check"])
        assert result.exit_code == 0
        assert result.output.strip() == "UPGRADE_AVAILABLE 0.6.0 0.9.0"
        assert uc._read_text(uc._cache_path()) == "UPGRADE_AVAILABLE 0.6.0 0.9.0"

    def test_fresh_cache_replays_without_fetching(self, tmp_home, monkeypatch: pytest.MonkeyPatch) -> None:
        _seed_cache("UPGRADE_AVAILABLE 0.6.0 0.9.0")

        def _boom() -> str:
            raise AssertionError("fetch must not happen on a fresh cache")

        monkeypatch.setattr(uc, "_fetch_latest", _boom)
        result = runner.invoke(app, ["upgrade-check"])
        assert result.output.strip() == "UPGRADE_AVAILABLE 0.6.0 0.9.0"


class TestQuietPaths:
    def test_up_to_date_is_silent(self, tmp_home, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(uc, "_fetch_latest", lambda: "0.6.0")
        result = runner.invoke(app, ["upgrade-check"])
        assert result.output.strip() == ""

    def test_offline_is_silent(self, tmp_home, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(uc, "_fetch_latest", lambda: None)
        result = runner.invoke(app, ["upgrade-check"])
        assert result.output.strip() == ""

    def test_opt_out_env_silences(self, tmp_home, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(uc, "_fetch_latest", lambda: "0.9.0")
        monkeypatch.setenv("ONEPIN_NO_UPDATE_CHECK", "1")
        result = runner.invoke(app, ["upgrade-check"])
        assert result.output.strip() == ""


class TestSnooze:
    def test_escalates_and_silences(self, tmp_home, monkeypatch: pytest.MonkeyPatch) -> None:
        _seed_cache("UPGRADE_AVAILABLE 0.6.0 0.9.0")
        # First decline -> level 1.
        runner.invoke(app, ["upgrade-check", "--snooze"])
        snooze = uc._read_text(uc._snooze_path()).split()
        assert snooze[0] == "0.9.0" and snooze[1] == "1"
        # While snoozed for this version, the prompt stays quiet.
        monkeypatch.setattr(uc, "_fetch_latest", lambda: "0.9.0")
        assert runner.invoke(app, ["upgrade-check"]).output.strip() == ""
        # Second decline -> level 2 (escalation).
        runner.invoke(app, ["upgrade-check", "--snooze"])
        assert uc._read_text(uc._snooze_path()).split()[1] == "2"

    def test_new_version_resets_snooze(self, tmp_home, monkeypatch: pytest.MonkeyPatch) -> None:
        _seed_cache("UPGRADE_AVAILABLE 0.6.0 0.9.0")
        runner.invoke(app, ["upgrade-check", "--snooze"])  # snooze 0.9.0
        # A newer release appears; the snooze for 0.9.0 must not suppress 0.9.5.
        _seed_cache("UPGRADE_AVAILABLE 0.6.0 0.9.5")
        monkeypatch.setattr(uc, "_fetch_latest", lambda: "0.9.5")
        result = runner.invoke(app, ["upgrade-check"])
        assert result.output.strip() == "UPGRADE_AVAILABLE 0.6.0 0.9.5"


class TestMarkUpgrading:
    def test_mark_then_just_upgraded(self, tmp_home, monkeypatch: pytest.MonkeyPatch) -> None:
        # "Upgrade now" writes the marker at the current version...
        runner.invoke(app, ["upgrade-check", "--mark-upgrading"])
        assert uc._marker_path().read_text().strip() == "0.6.0"
        # ...then after pip bumps the version, the next run confirms the upgrade.
        monkeypatch.setattr(uc, "__version__", "0.9.0")
        result = runner.invoke(app, ["upgrade-check"])
        assert result.output.strip() == "JUST_UPGRADED 0.6.0 0.9.0"


class TestMarker:
    def test_just_upgraded(self, tmp_home) -> None:
        marker = uc._marker_path()
        marker.parent.mkdir(parents=True, exist_ok=True)
        marker.write_text("0.5.0\n", encoding="utf-8")
        result = runner.invoke(app, ["upgrade-check"])
        assert result.output.strip() == "JUST_UPGRADED 0.5.0 0.6.0"
        assert not marker.exists()


class TestCachedLatest:
    def test_reads_latest_regardless_of_freshness(self, tmp_home) -> None:
        assert uc.cached_latest() is None
        _seed_cache("UPGRADE_AVAILABLE 0.6.0 0.9.0")
        assert uc.cached_latest() == "0.9.0"
        _seed_cache("UP_TO_DATE 0.6.0")
        assert uc.cached_latest() == "0.6.0"


class TestDisable:
    def test_disable_silences_future_checks(self, tmp_home, monkeypatch: pytest.MonkeyPatch) -> None:
        runner.invoke(app, ["upgrade-check", "--disable"])
        assert uc._disabled_path().exists()
        # Even with an upgrade available, a disabled check stays silent and skips the fetch.
        monkeypatch.setattr(uc, "_fetch_latest", lambda: "0.9.0")
        result = runner.invoke(app, ["upgrade-check"])
        assert result.output.strip() == ""


class TestFetchLatest:
    @respx.mock
    def test_returns_pypi_version(self, tmp_home) -> None:
        respx.get(uc._PYPI_URL).mock(return_value=httpx.Response(200, json={"info": {"version": "1.2.3"}}))
        assert uc._fetch_latest() == "1.2.3"

    @respx.mock
    def test_non_200_is_none(self, tmp_home) -> None:
        respx.get(uc._PYPI_URL).mock(return_value=httpx.Response(503))
        assert uc._fetch_latest() is None

    @respx.mock
    def test_unparseable_version_is_none(self, tmp_home) -> None:
        respx.get(uc._PYPI_URL).mock(return_value=httpx.Response(200, json={"info": {"version": "nightly"}}))
        assert uc._fetch_latest() is None


class TestEdgeBranches:
    def test_force_refetches(self, tmp_home, monkeypatch: pytest.MonkeyPatch) -> None:
        _seed_cache("UPGRADE_AVAILABLE 0.6.0 9.9.9")
        monkeypatch.setattr(uc, "_fetch_latest", lambda: "0.6.0")  # now up to date
        result = runner.invoke(app, ["upgrade-check", "--force"])
        assert result.output.strip() == ""
        assert uc._read_text(uc._cache_path()) == "UP_TO_DATE 0.6.0"

    def test_snooze_without_cached_upgrade_is_noop(self, tmp_home) -> None:
        runner.invoke(app, ["upgrade-check", "--snooze"])
        assert not uc._snooze_path().exists()

    def test_stale_cache_triggers_refetch(self, tmp_home, monkeypatch: pytest.MonkeyPatch) -> None:
        import os
        import time

        _seed_cache("UP_TO_DATE 0.6.0")
        old = time.time() - (uc._TTL_UP_TO_DATE + 5) * 60
        os.utime(uc._cache_path(), (old, old))
        monkeypatch.setattr(uc, "_fetch_latest", lambda: "0.9.0")
        result = runner.invoke(app, ["upgrade-check"])
        assert result.output.strip() == "UPGRADE_AVAILABLE 0.6.0 0.9.0"  # stale -> refetched

    def test_garbage_cache_is_none(self, tmp_home) -> None:
        _seed_cache("garbage line here")
        assert uc.cached_latest() is None
