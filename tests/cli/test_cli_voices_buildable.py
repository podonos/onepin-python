"""``voices list --buildable``: the gate, its precondition, and what it refuses to claim.

These go through respx rather than a fake client because most of what is being asserted is
*wire* behaviour -- which query keys go out, how a repeated filter is encoded, and what the CLI
concludes from a server that answers the gate by ignoring it. A fake client cannot be wrong
about any of those, so it cannot catch them being wrong either.
"""

from __future__ import annotations

from urllib.parse import parse_qsl, urlsplit

import httpx
import pytest
import respx
from typer.testing import CliRunner

from onepin._cli.main import app

runner = CliRunner()
_BASE = "https://api.onepin.ai"
_VOICES = f"{_BASE}/api/v1/voices"

_META = {"request_id": "01JTEST00000000000000000000", "timestamp": "2025-01-01T00:00:00Z"}

_VOICE_ROW = {
    "id": "voice-1",
    "name": "Haneul",
    "provider": "elevenlabs",
    "provider_voice_id": "pv-1",
    "is_active": True,
    "created_at": "2025-01-01T00:00:00Z",
    "updated_at": "2025-01-01T00:00:00Z",
    "gender": "female",
    "category": "narration",
}

#: How the API answers `?buildable=true` with no `language`. Its presence is what proves the
#: server declares the parameter at all -- see BuildableGate.probe.
_REQUIRES_LANGUAGE_422 = {
    "error": {
        "code": "VALIDATION_ERROR",
        "message": "Some request fields need attention.",
        "details": [{"field": "buildable", "reason": "requires_language"}],
    },
    "meta": _META,
}


def _page(rows: list[dict], total: int | None = None) -> dict:
    return {
        "data": rows,
        "meta": _META,
        "pagination": {"next": None, "prev": None, "limit": 50, "total": len(rows) if total is None else total},
    }


def _invoke(argv: list[str]):
    return runner.invoke(app, ["--api-key", "op_live_x", *argv])


def _queries(route) -> list[list[tuple[str, str]]]:
    """Every request the route saw, as an ordered list of raw query pairs.

    Ordered pairs, not a dict: whether a repeated filter went out as two keys or one joined
    value is exactly the thing being asserted, and a dict erases the difference.
    """
    return [parse_qsl(urlsplit(str(call.request.url)).query) for call in route.calls]


def _supported_server(rows: list[dict], *, total: int | None = None):
    """Route `GET /voices` so the probe sees a 422 and the real call sees a gated page.

    The two are told apart by `language`: the probe deliberately omits it (that is how it asks
    the question), the real call always carries it because the CLI requires it.
    """

    def handler(request: httpx.Request) -> httpx.Response:
        if "language" not in dict(parse_qsl(urlsplit(str(request.url)).query)):
            return httpx.Response(422, json=_REQUIRES_LANGUAGE_422)
        return httpx.Response(200, json=_page(rows, total))

    return respx.get(url__startswith=_VOICES).mock(side_effect=handler)


class TestFlagReachesTheWire:
    """R1: the flag exists, maps to `?buildable=true`, and is off unless asked for."""

    @respx.mock
    def test_buildable_sends_the_query_parameter(self, tmp_home) -> None:
        route = _supported_server([_VOICE_ROW])

        result = _invoke(["voices", "list", "--language", "ko-kr", "--buildable", "--json"])

        assert result.exit_code == 0, result.output
        real_call = _queries(route)[-1]
        assert ("buildable", "true") in real_call
        assert ("language", "ko-kr") in real_call

    @respx.mock
    def test_default_is_off_and_sends_nothing(self, tmp_home) -> None:
        route = respx.get(url__startswith=_VOICES).mock(return_value=httpx.Response(200, json=_page([_VOICE_ROW])))

        result = _invoke(["voices", "list", "--language", "ko-kr", "--json"])

        assert result.exit_code == 0, result.output
        # Not `buildable=false` either: the server default already is false, and sending it
        # would make an old server look gated for the same reason a new one is.
        assert [key for key, _ in _queries(route)[0]].count("buildable") == 0
        # No probe either -- an ungated list has nothing to verify.
        assert len(route.calls) == 1

    @respx.mock
    def test_json_payload_stays_a_bare_array(self, tmp_home) -> None:
        _supported_server([_VOICE_ROW])

        result = _invoke(["voices", "list", "--language", "ko-kr", "--buildable", "--json"])

        assert result.exit_code == 0, result.output
        assert result.stdout.lstrip().startswith("[")
        # The gate narrates on stderr precisely so the stdout contract does not move.
        assert "buildable" in result.stderr


class TestRequiresLanguage:
    """R2: refuse the combination the server cannot evaluate, before spending a request."""

    @respx.mock
    def test_buildable_without_language_is_a_usage_error(self, tmp_home) -> None:
        route = respx.get(url__startswith=_VOICES).mock(return_value=httpx.Response(200, json=_page([])))

        result = _invoke(["voices", "list", "--buildable"])

        assert result.exit_code == 2, result.output
        assert "--language" in result.output
        assert not route.calls, "the CLI asked the server a question it had already been told is invalid"

    @respx.mock
    def test_blank_language_does_not_satisfy_the_precondition(self, tmp_home) -> None:
        route = respx.get(url__startswith=_VOICES).mock(return_value=httpx.Response(200, json=_page([])))

        result = _invoke(["voices", "list", "--language", " , ", "--buildable"])

        assert result.exit_code == 2, result.output
        assert not route.calls

    @respx.mock
    def test_server_side_rejection_is_rewritten(self, tmp_home) -> None:
        """A `--language` that resolves to no supported locale 422s the same way; say so."""

        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(422, json=_REQUIRES_LANGUAGE_422)

        respx.get(url__startswith=_VOICES).mock(side_effect=handler)

        result = _invoke(["voices", "list", "--language", "zz-zz", "--buildable", "--json"])

        assert result.exit_code == 1, result.output
        assert "BUILDABLE_REQUIRES_LANGUAGE" in result.output
        assert "voices facets" in result.output
        # The raw envelope's own vocabulary must not be what the user is handed.
        assert "requires_language" not in result.output


class TestEmptyResultMeaning:
    """R3: zero gated rows is a statement about the gate, not about the catalogue."""

    @respx.mock
    def test_zero_rows_blames_the_gate_not_the_catalogue(self, tmp_home) -> None:
        _supported_server([], total=0)

        result = _invoke(["voices", "list", "--language", "ko-kr", "--buildable"])

        assert result.exit_code == 0, result.output
        assert "not an empty catalog" in result.stderr
        assert "pagination.total" in result.stderr
        assert "without --buildable" in result.stderr

    @respx.mock
    def test_non_empty_result_still_says_the_gate_is_on(self, tmp_home) -> None:
        _supported_server([_VOICE_ROW])

        result = _invoke(["voices", "list", "--language", "ko-kr", "--buildable"])

        assert result.exit_code == 0, result.output
        assert "--buildable is on" in result.stderr

    @respx.mock
    def test_ungated_empty_result_says_nothing_about_a_gate(self, tmp_home) -> None:
        respx.get(url__startswith=_VOICES).mock(return_value=httpx.Response(200, json=_page([])))

        result = _invoke(["voices", "list", "--language", "ko-kr"])

        assert result.exit_code == 0, result.output
        assert "buildable" not in result.stderr


class TestOverstatement:
    """R10: the gate excludes transient provider health, so it cannot promise a run."""

    @respx.mock
    def test_note_does_not_promise_the_run_will_succeed(self, tmp_home) -> None:
        _supported_server([_VOICE_ROW])

        result = _invoke(["voices", "list", "--language", "ko-kr", "--buildable"])

        assert "a run can still fail" in result.stderr
        assert "guarantee" not in result.stderr.lower()

    @respx.mock
    def test_note_warns_against_storing_the_verdict(self, tmp_home) -> None:
        """R9: buildability tracks live provider routing, so it is not a fact about a voice."""
        _supported_server([_VOICE_ROW])

        result = _invoke(["voices", "list", "--language", "ko-kr", "--buildable"])

        assert "do not store this" in result.stderr


class TestRepeatedLanguageKeys:
    """R6: repeated keys, never one comma-joined value the server would read as a single locale."""

    @respx.mock
    def test_multi_language_goes_out_as_repeated_keys(self, tmp_home) -> None:
        route = _supported_server([_VOICE_ROW])

        result = _invoke(["voices", "list", "--language", "ko-kr,en-us", "--buildable", "--json"])

        assert result.exit_code == 0, result.output
        languages = [value for key, value in _queries(route)[-1] if key == "language"]
        assert languages == ["ko-kr", "en-us"]

    @respx.mock
    def test_multi_language_without_the_gate_too(self, tmp_home) -> None:
        route = respx.get(url__startswith=_VOICES).mock(return_value=httpx.Response(200, json=_page([_VOICE_ROW])))

        result = _invoke(["voices", "list", "--language", "ko-kr,en-us", "--json"])

        assert result.exit_code == 0, result.output
        assert [value for key, value in _queries(route)[0] if key == "language"] == ["ko-kr", "en-us"]


class TestOldServerIsNotSilentlyUngated:
    """R8: the dangerous failure is a correct-looking list, so it has to be refused."""

    @respx.mock
    def test_server_that_ignores_the_parameter_is_refused(self, tmp_home) -> None:
        # An API without `buildable` does not error on it -- FastAPI drops unknown query
        # parameters -- so the probe's `?buildable=true` with no `language` comes back 200.
        route = respx.get(url__startswith=_VOICES).mock(return_value=httpx.Response(200, json=_page([_VOICE_ROW])))

        result = _invoke(["voices", "list", "--language", "ko-kr", "--buildable"])

        assert result.exit_code == 1, result.output
        assert "BUILDABLE_UNSUPPORTED" in result.output
        # Refused at the probe: the ungated page was never fetched, let alone printed.
        assert len(route.calls) == 1
        assert "Haneul" not in result.stdout

    @respx.mock
    def test_unverifiable_server_lists_but_claims_nothing(self, tmp_home) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            query = dict(parse_qsl(urlsplit(str(request.url)).query))
            if "language" not in query:
                return httpx.Response(503, json={"error": {"code": "SERVER_ERROR", "message": "nope"}})
            return httpx.Response(200, json=_page([_VOICE_ROW]))

        respx.get(url__startswith=_VOICES).mock(side_effect=handler)

        result = _invoke(["voices", "list", "--language", "ko-kr", "--buildable"])

        assert result.exit_code == 0, result.output
        assert "could not be confirmed" in result.stderr
        assert "UNFILTERED" in result.stderr
        assert "--buildable is on" not in result.stderr

    @respx.mock
    def test_unreachable_probe_lists_but_claims_nothing(self, tmp_home) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            query = dict(parse_qsl(urlsplit(str(request.url)).query))
            if "language" not in query:
                raise httpx.ConnectTimeout("probe timed out")
            return httpx.Response(200, json=_page([_VOICE_ROW]))

        respx.get(url__startswith=_VOICES).mock(side_effect=handler)

        result = _invoke(["voices", "list", "--language", "ko-kr", "--buildable"])

        assert result.exit_code == 0, result.output
        assert "could not be confirmed" in result.stderr

    @respx.mock
    def test_probe_is_scoped_to_the_active_workspace(self, tmp_home) -> None:
        route = _supported_server([_VOICE_ROW])

        result = runner.invoke(
            app,
            ["--api-key", "op_live_x", "--workspace", "ws-1", "voices", "list", "--language", "ko-kr", "--buildable"],
        )

        assert result.exit_code == 0, result.output
        probe = route.calls[0].request
        assert probe.headers.get("X-Workspace-Id") == "ws-1"

    @respx.mock
    def test_probe_is_asked_once_per_process(self, tmp_home) -> None:
        route = _supported_server([_VOICE_ROW])

        assert _invoke(["voices", "list", "--language", "ko-kr", "--buildable", "--json"]).exit_code == 0
        assert _invoke(["voices", "list", "--language", "en-us", "--buildable", "--json"]).exit_code == 0

        probes = [query for query in _queries(route) if "language" not in dict(query)]
        assert len(probes) == 1


class TestGateStaysOnList:
    """R5: `show` and `similar` already have an id; there is nothing for a gate to narrow."""

    @pytest.mark.parametrize("argv", [["voices", "show", "voice-1"], ["voices", "similar", "voice-1"]])
    def test_other_voice_commands_reject_the_flag(self, argv: list[str], tmp_home) -> None:
        result = _invoke([*argv, "--buildable"])

        assert result.exit_code == 2, result.output

    def test_facets_rejects_the_flag(self, tmp_home) -> None:
        # `GET /voices/facets` does not take the parameter: a chip count is evaluated per
        # dimension, and the language dimension self-excludes the very filter the gate needs.
        result = _invoke(["voices", "facets", "--buildable"])

        assert result.exit_code == 2, result.output
