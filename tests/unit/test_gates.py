"""Unit tests for the gate machinery: preconditions, the SDK bridge, and the capability probe.

The CLI-level tests in ``tests/cli/test_cli_voices_buildable.py`` cover the wire behaviour.
These cover the pieces that decide it, including the shapes the probe must NOT read as a
verdict -- a wrong "supported" is the whole failure this design exists to prevent.
"""

from __future__ import annotations

import inspect
from types import SimpleNamespace

import httpx
import pytest

from onepin._cli import _dispatch
from onepin._cli._ctx import CliError
from onepin._cli._gates import BuildableGate, Support, get_gate, requires_language_detail
from onepin._cli._spec import Cmd, Opt

_REQUIRES_LANGUAGE = {
    "error": {
        "code": "VALIDATION_ERROR",
        "message": "Some request fields need attention.",
        "details": [{"field": "buildable", "reason": "requires_language"}],
    }
}


def _response(status: int, json_body: object | None = None, *, text: str | None = None) -> httpx.Response:
    if text is not None:
        return httpx.Response(status, text=text)
    return httpx.Response(status, json=json_body)


class TestRequiresLanguageDetail:
    def test_matches_the_documented_shape(self) -> None:
        assert requires_language_detail(_REQUIRES_LANGUAGE)

    def test_matches_a_flat_details_envelope(self) -> None:
        assert requires_language_detail({"details": [{"field": "buildable", "reason": "requires_language"}]})

    @pytest.mark.parametrize(
        "body",
        [
            None,
            "not a dict",
            {},
            {"error": {"details": "not-a-list"}},
            # A generic FastAPI validation detail: same endpoint, same status, different field.
            {"error": {"details": [{"field": "header.Authorization", "message": "Field required"}]}},
            # Right field, wrong reason -- some other precondition on the same parameter.
            {"error": {"details": [{"field": "buildable", "reason": "something_else"}]}},
            # Right reason, wrong field.
            {"error": {"details": [{"field": "language", "reason": "requires_language"}]}},
        ],
    )
    def test_rejects_everything_else(self, body: object) -> None:
        assert not requires_language_detail(body)


class TestProbeVerdicts:
    def test_422_with_the_detail_is_supported(self) -> None:
        assert BuildableGate._verdict(_response(422, _REQUIRES_LANGUAGE)).support is Support.YES

    def test_200_is_unsupported(self) -> None:
        """The parameter went out, the precondition was not enforced, a page came back."""
        assert BuildableGate._verdict(_response(200, {"data": []})).support is Support.NO

    @pytest.mark.parametrize("status", [401, 403, 426, 429, 500, 503])
    def test_other_statuses_are_unknown(self, status: int) -> None:
        verdict = BuildableGate._verdict(_response(status, {"error": {"code": "X"}}))
        assert verdict.support is Support.UNKNOWN
        assert verdict.detail

    def test_unrelated_422_is_unknown_not_supported(self) -> None:
        """A 422 about the API key says nothing about `buildable`; it never got judged."""
        body = {"error": {"details": [{"field": "header.Authorization", "message": "Field required"}]}}

        assert BuildableGate._verdict(_response(422, body)).support is Support.UNKNOWN

    def test_unreadable_422_is_unknown(self) -> None:
        assert BuildableGate._verdict(_response(422, text="<html>gateway</html>")).support is Support.UNKNOWN


class TestPreflight:
    def test_known_unsupported_refuses(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(BuildableGate, "probe", classmethod(lambda cls, *a, **k: _probe(Support.NO)))

        with pytest.raises(CliError) as excinfo:
            BuildableGate.preflight(SimpleNamespace(api_key="k", base_url=None), None)

        assert excinfo.value.code == "BUILDABLE_UNSUPPORTED"
        assert "without --buildable" in excinfo.value.message

    def test_unknown_is_allowed_through(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(BuildableGate, "probe", classmethod(lambda cls, *a, **k: _probe(Support.UNKNOWN, "why")))

        assert BuildableGate.preflight(SimpleNamespace(api_key="k", base_url=None), None).support is Support.UNKNOWN


def _probe(support: Support, detail: str = ""):
    from onepin._cli._gates import ProbeResult

    return ProbeResult(support, detail)


class TestTranslateError:
    def test_rewrites_the_gates_own_422(self) -> None:
        exc = SimpleNamespace(status_code=422, body=_REQUIRES_LANGUAGE)

        translated = BuildableGate.translate_error(exc)  # type: ignore[arg-type]

        assert translated is not None
        assert translated.code == "BUILDABLE_REQUIRES_LANGUAGE"

    def test_leaves_an_unrelated_422_alone(self) -> None:
        exc = SimpleNamespace(status_code=422, body={"error": {"details": [{"field": "limit"}]}})

        assert BuildableGate.translate_error(exc) is None  # type: ignore[arg-type]

    def test_leaves_a_non_422_alone(self) -> None:
        assert BuildableGate.translate_error(SimpleNamespace(status_code=404, body=_REQUIRES_LANGUAGE)) is None  # type: ignore[arg-type]


class TestGateRegistry:
    def test_no_gate_declared(self) -> None:
        assert get_gate(None) is None

    def test_unknown_gate_is_an_internal_error(self) -> None:
        with pytest.raises(CliError) as excinfo:
            get_gate("not-a-gate")

        assert excinfo.value.code == "INTERNAL"


class TestCheckRequires:
    def _cmd(self) -> Cmd:
        return Cmd(
            "voices",
            "list",
            "voices.list",
            "x",
            options=[
                Opt("--language", "str", None, transform="comma_list"),
                Opt(
                    "--buildable",
                    "bool",
                    False,
                    requires=("--language",),
                    requires_note="measured per locale.",
                    help="Needs a locale.",
                ),
            ],
        )

    def test_passes_when_the_requirement_is_met(self) -> None:
        _dispatch._check_requires(self._cmd(), {"language": "ko-kr", "buildable": True})

    def test_passes_when_the_requiring_flag_is_off(self) -> None:
        _dispatch._check_requires(self._cmd(), {"language": None, "buildable": False})

    def test_fails_when_the_requirement_is_missing(self) -> None:
        import typer

        with pytest.raises(typer.BadParameter) as excinfo:
            _dispatch._check_requires(self._cmd(), {"language": None, "buildable": True})

        message = str(excinfo.value)
        assert "--buildable requires --language" in message
        # The reason, not just the refusal -- otherwise "add it" and "drop it" look equally right.
        assert "measured per locale." in message

    @pytest.mark.parametrize("language", ["", " ", ",", " , "])
    def test_a_value_that_sends_nothing_does_not_count_as_set(self, language: str) -> None:
        """`--language ,` parses, transforms to [], and reaches the server as no locale at all."""
        import typer

        with pytest.raises(typer.BadParameter):
            _dispatch._check_requires(self._cmd(), {"language": language, "buildable": True})

    def test_an_explicit_off_on_a_tristate_requirement_counts_as_set(self) -> None:
        """A tri-state `--no-x` is a forwarded value, so it satisfies a precondition on it.

        This is the rule `_build_kwargs` uses to decide what reaches the SDK; `_is_set` follows
        it rather than inventing a second one, so the check can never refuse a combination the
        request would have carried fine.
        """
        cmd = Cmd(
            "workflows",
            "list",
            "workflows.list",
            "x",
            options=[
                Opt("--has-failed-run/--no-has-failed-run", "bool", None),
                Opt("--sort", "str", None, requires=("--has-failed-run",)),
            ],
        )

        _dispatch._check_requires(cmd, {"has_failed_run": False, "sort": "name"})


class TestSpecIntegrity:
    def test_every_requires_entry_names_a_real_sibling_flag(self) -> None:
        """A `requires` that resolves to nothing reads as "always missing" and refuses everything.

        The failure is silent in exactly the wrong direction -- a typo'd flag name makes the
        option permanently unusable rather than permanently unchecked -- so pin it here.
        """
        from onepin._cli._spec import TABLE

        for cmd in TABLE:
            spellings = {alias.split("/")[0] for opt in cmd.options for alias in opt.flag.split()}
            for opt in cmd.options:
                unknown = set(opt.requires) - spellings
                assert not unknown, f"{'.'.join(cmd.path)}: {opt.flag} requires {sorted(unknown)}, not a flag it has"

    def test_a_requires_entry_carries_its_reason(self) -> None:
        from onepin._cli._spec import TABLE

        for cmd in TABLE:
            for opt in cmd.options:
                if opt.requires:
                    assert opt.requires_note.strip(), f"{'.'.join(cmd.path)}: {opt.flag} refuses without saying why"


class TestQueryFallback:
    """R7's bridge: reach a live API parameter the generated SDK has not caught up to yet."""

    def _cmd(self) -> Cmd:
        return Cmd(
            "voices",
            "list",
            "voices.list",
            "x",
            options=[Opt("--buildable", "bool", False, query_fallback=True)],
        )

    def test_bridged_when_the_method_lacks_the_keyword(self) -> None:
        def old_sdk(*, language=None, request_options=None):
            return None

        kwargs = {"language": ["ko-kr"], "buildable": True}
        _dispatch._apply_query_fallbacks(self._cmd(), old_sdk, kwargs)

        assert "buildable" not in kwargs
        assert kwargs["request_options"]["additional_query_parameters"] == {"buildable": True}
        assert kwargs["language"] == ["ko-kr"]

    def test_native_once_the_method_grows_the_keyword(self) -> None:
        def new_sdk(*, language=None, buildable=None, request_options=None):
            return None

        kwargs = {"language": ["ko-kr"], "buildable": True}
        _dispatch._apply_query_fallbacks(self._cmd(), new_sdk, kwargs)

        assert kwargs["buildable"] is True
        assert "request_options" not in kwargs

    def test_existing_request_options_are_preserved(self) -> None:
        def old_sdk(*, request_options=None):
            return None

        kwargs = {
            "buildable": True,
            "request_options": {"timeout": 5, "additional_query_parameters": {"other": "x"}},
        }
        _dispatch._apply_query_fallbacks(self._cmd(), old_sdk, kwargs)

        assert kwargs["request_options"]["timeout"] == 5
        assert kwargs["request_options"]["additional_query_parameters"] == {"other": "x", "buildable": True}

    def test_untouched_when_the_flag_is_absent(self) -> None:
        def old_sdk(*, request_options=None):
            return None

        kwargs: dict = {}
        _dispatch._apply_query_fallbacks(self._cmd(), old_sdk, kwargs)

        assert kwargs == {}

    def test_kwargs_accepting_method_is_left_native(self) -> None:
        """A **kwargs fake (or a future SDK shape) can take the keyword as-is."""

        def anything(**kwargs):
            return None

        kwargs = {"buildable": True}
        _dispatch._apply_query_fallbacks(self._cmd(), anything, kwargs)

        assert kwargs == {"buildable": True}

    def test_the_live_spec_row_is_wired_for_the_real_sdk(self) -> None:
        """Whatever the installed SDK does, `--buildable` must end up on the query string."""
        from onepin._cli._spec import TABLE

        cmd = next(row for row in TABLE if row.path == ("voices", "list"))
        method = _fake_signature_of_real_voices_list()
        kwargs = {"language": ["ko-kr"], "buildable": True}

        _dispatch._apply_query_fallbacks(cmd, method, kwargs)

        sent = kwargs.get("buildable") or kwargs["request_options"]["additional_query_parameters"]["buildable"]
        assert sent is True


def _fake_signature_of_real_voices_list():
    """A stand-in carrying the installed SDK's actual `voices.list` signature."""
    from onepin.client import OnePinClient

    real = OnePinClient(token="op_live_test").voices.list

    def stub(*args, **kwargs):
        return None

    stub.__signature__ = inspect.signature(real)  # type: ignore[attr-defined]
    return stub
