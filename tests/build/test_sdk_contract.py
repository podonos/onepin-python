"""Contract test: the CLI surface and the real Fern SDK must agree, in both directions.

Auto-derived from :data:`onepin._cli._spec.TABLE`. For each command this asserts that:

- the dotted ``method`` path resolves to a callable on a built client,
- each positional arg and each forwarded option ``dest`` is a parameter the method accepts
  (or the method accepts ``**kwargs``),
- every parameter the method marks *required* is supplied by the row (positional, option,
  or const), and
- every parameter the method *accepts* is either reachable from the CLI or listed in
  :data:`_INTENTIONALLY_UNEXPOSED` with a reason.

The first three are the CLI -> SDK direction: they fail loudly if a Fern regen renames or
drops a method/param the CLI depends on.

The last one is SDK -> CLI, and it is the direction that actually goes wrong here. The
BE -> SDK half of the pipeline is automatic, so a new query parameter lands in
``src/onepin/<resource>/client.py`` on the next regen with nobody in the loop; the SDK -> CLI
half is hand-written, so it lands nowhere. Nothing was red while ``GET /voices`` grew
``age``/``category``/``accent`` and ``voices list`` kept offering four of its eight filters
for months -- the discovery path was a user saying the agent behaved oddly, not a test. Since
``.github/workflows/regen.yml`` already runs ``tests/build`` on every generated PR, asserting
the reverse direction here turns that silence into a failing check on the regen PR itself.

Both directions are then repeated for the hand-written composites, which are not TABLE rows and
which every parametrized check above therefore skips. See :data:`_COMPOSITE_CALLS`.
"""

from __future__ import annotations

import inspect
from typing import get_args

import pytest

from onepin._cli._dispatch import _accepts_workspace_kwarg, _resolve_method
from onepin._cli._spec import TABLE, Cmd
from onepin.client import OnePinClient
from onepin.types import NodeType

# Options whose dest is consumed by the CLI itself, not forwarded to the SDK.
_LOCAL_DESTS = {"json_output_local", "reveal", "yes"}
_LOCAL_FLAGS = {"--json", "--reveal", "--yes"}

# Never a CLI flag on any command: `self` is the bound receiver and `request_options` is the
# SDK's per-call transport knob (retries, timeout, extra headers), which the CLI configures
# from the environment rather than per invocation.
_NEVER_A_FLAG = {"self", "request_options"}

# SDK params a command deliberately does not expose, keyed by command path, valued by reason.
#
# This exists to keep "we decided not to" distinguishable from "nobody noticed". Those two
# look identical in a command table -- which is exactly how the voice filters sat unexposed --
# so an entry here is a decision written down, and `test_allowlist_has_no_stale_entries`
# deletes it the moment it stops being true.
_INTENTIONALLY_UNEXPOSED: dict[tuple[str, ...], dict[str, str]] = {}


def _resolve_cmd_method(cmd: Cmd):
    client = OnePinClient(token="op_live_test")
    return _resolve_method(client, cmd.method_paths)


def _node_type_option():
    cmd = next(cmd for cmd in TABLE if cmd.path == ("workflows", "runs", "steps"))
    return next(option for option in cmd.options if option.flag == "--node-type")


def test_run_steps_node_type_choices_match_public_type() -> None:
    """The --node-type choices must stay equal to the generated NodeType.

    This passes by construction while `_spec._NODE_TYPES` derives from `NodeType`; it exists to
    fail if someone re-hardcodes the tuple, which is what previously made every regen that added
    a node type break the build.
    """
    public_values = tuple(
        value for branch in get_args(NodeType) for value in get_args(branch) if isinstance(value, str)
    )

    assert _node_type_option().type == public_values


def test_node_type_choices_are_not_empty() -> None:
    """Guard the derivation itself.

    Deriving from `NodeType` is only safe while `get_args` actually yields the literals. If a
    future Fern release emits `NodeType` in another shape, the comprehension would quietly
    produce `()` and `--node-type` would accept nothing — equal to the (also empty) expectation
    above, so the test there could not catch it. Anchor on literals the API is not going to drop.
    """
    choices = _node_type_option().type

    assert isinstance(choices, tuple)
    assert {"source_script", "operator_generator"} <= set(choices), (
        f"NodeType derivation yielded {choices!r} — the generated NodeType shape likely changed"
    )


@pytest.mark.parametrize("cmd", TABLE, ids=lambda c: ".".join(c.path))
def test_method_resolves(cmd: Cmd) -> None:
    method = _resolve_cmd_method(cmd)
    assert callable(method), f"{cmd.method} is not callable"


@pytest.mark.parametrize("cmd", TABLE, ids=lambda c: ".".join(c.path))
def test_declared_params_subset_of_signature(cmd: Cmd) -> None:
    method = _resolve_cmd_method(cmd)
    sig = inspect.signature(method)
    params = sig.parameters
    accepts_kwargs = any(p.kind == inspect.Parameter.VAR_KEYWORD for p in params.values())

    declared = [dest for dest, _ in cmd.args]
    for opt in cmd.options:
        flag = opt.flag.split()[0]
        if opt.dest_name in _LOCAL_DESTS or flag in _LOCAL_FLAGS:
            continue
        # A `query_fallback` option is declared against the *spec*, not against this SDK
        # snapshot: it exists because the parameter shipped server-side and this repo has not
        # regenerated yet. The dispatcher routes it through
        # request_options.additional_query_parameters exactly while it is missing here, so
        # "the method does not accept it" is the expected state, not the drift this asserts.
        # `test_query_fallback_is_still_needed` is the check that ends that state.
        if opt.query_fallback:
            continue
        declared.append(opt.dest_name)
    declared.extend(cmd.consts.keys())

    if accepts_kwargs:
        return
    for name in declared:
        assert name in params, f"{cmd.method} does not accept declared param {name!r} (have {list(params)})"


def _query_fallback_opts() -> list[tuple[Cmd, str]]:
    return [(cmd, opt.dest_name) for cmd in TABLE for opt in cmd.options if opt.query_fallback]


@pytest.mark.parametrize(
    ("cmd", "dest"), _query_fallback_opts(), ids=lambda value: value if isinstance(value, str) else ".".join(value.path)
)
def test_query_fallback_is_still_needed(cmd: Cmd, dest: str) -> None:
    """A `query_fallback` bridge must disappear the moment the SDK grows the real keyword.

    The bridge is a workaround for one window -- the parameter is live on the API, and the
    generated client has not caught up. Left in place past that window it is a second, dimmer
    code path for something the SDK now does natively, and the kind of thing that is only
    found when it breaks. Failing here on the regen PR that closes the gap is what makes it
    get deleted then, rather than becoming permanent.
    """
    params = inspect.signature(_resolve_cmd_method(cmd)).parameters

    assert dest not in params, (
        f"{'.'.join(cmd.path)}: {cmd.method} now accepts {dest!r} natively, so the "
        f"query_fallback=True bridge on that Opt is dead code — drop it from _spec.py."
    )


@pytest.mark.parametrize("cmd", TABLE, ids=lambda c: ".".join(c.path))
def test_required_params_supplied(cmd: Cmd) -> None:
    method = _resolve_cmd_method(cmd)
    sig = inspect.signature(method)

    supplied = {dest for dest, _ in cmd.args}
    supplied |= set(cmd.consts.keys())
    for opt in cmd.options:
        flag = opt.flag.split()[0]
        if opt.dest_name in _LOCAL_DESTS or flag in _LOCAL_FLAGS:
            continue
        supplied.add(opt.dest_name)
    # The dispatcher conditionally forwards workspace_id from the root flag.
    supplied.add("workspace_id")

    for name, param in sig.parameters.items():
        if name in ("self", "request_options"):
            continue
        if param.kind in (inspect.Parameter.VAR_KEYWORD, inspect.Parameter.VAR_POSITIONAL):
            continue
        required = param.default is inspect.Parameter.empty
        if required:
            assert name in supplied, f"{cmd.method} requires {name!r} but the TABLE row does not supply it"


def _exposed_dests(cmd: Cmd) -> set[str]:
    """Every SDK keyword a user can reach from this command's flags, args and consts."""
    exposed = {dest for dest, _ in cmd.args} | set(cmd.consts)
    for opt in cmd.options:
        if opt.dest_name in _LOCAL_DESTS or opt.flag.split()[0] in _LOCAL_FLAGS:
            continue
        exposed.add(opt.dest_name)
    return exposed


def _accepted_params(method) -> set[str]:
    """Every param of ``method`` a CLI flag could plausibly fill.

    ``workspace_id`` is excluded when the method takes it *keyword-only*, which is the SDK's
    workspace-scoping convention: the dispatcher fills that from the global ``--workspace`` /
    ``ONEPIN_WORKSPACE_ID``, so it is reachable without a per-command flag. A method whose
    ``workspace_id`` is positional is a path parameter instead and gets no such pass.
    """
    sig = inspect.signature(method)
    accepted = {
        name
        for name, param in sig.parameters.items()
        if param.kind not in (inspect.Parameter.VAR_KEYWORD, inspect.Parameter.VAR_POSITIONAL)
    } - _NEVER_A_FLAG
    if _accepts_workspace_kwarg(method):
        accepted.discard("workspace_id")
    return accepted


def _unexposed_params(cmd: Cmd) -> set[str]:
    """SDK params this command accepts but offers no way to set."""
    return _accepted_params(_resolve_cmd_method(cmd)) - _exposed_dests(cmd)


@pytest.mark.parametrize("cmd", TABLE, ids=lambda c: ".".join(c.path))
def test_no_unexposed_sdk_params(cmd: Cmd) -> None:
    """Every param the SDK accepts is reachable from the CLI, or allowlisted with a reason.

    This is the drift check the regen PR runs: the generated client gains a param, no
    hand-written flag gains with it, and this goes red naming the command and the param
    instead of leaving the gap to be found in use months later.
    """
    missing = _unexposed_params(cmd) - set(_INTENTIONALLY_UNEXPOSED.get(cmd.path, {}))

    assert not missing, (
        f"{'.'.join(cmd.path)}: {cmd.method} accepts {sorted(missing)} but the CLI has no flag "
        f"for it. Either add an Opt(...) to the row in _spec.py, or record the decision in "
        f"_INTENTIONALLY_UNEXPOSED with the reason."
    )


def test_allowlist_has_no_stale_entries() -> None:
    """The allowlist may only name gaps that are still gaps.

    An allowlist nobody prunes is worse than none: it silently keeps excusing a param that
    has since been exposed, or one the API dropped. Both mean the recorded reason no longer
    describes the code, so both fail here.
    """
    by_path = {cmd.path: cmd for cmd in TABLE}

    for path, reasons in _INTENTIONALLY_UNEXPOSED.items():
        cmd = by_path.get(path)
        assert cmd is not None, f"_INTENTIONALLY_UNEXPOSED names {path}, which is not a command in TABLE"
        assert reasons, f"{'.'.join(path)}: allowlist entry is empty — drop the key instead"
        stale = set(reasons) - _unexposed_params(cmd)
        assert not stale, (
            f"{'.'.join(path)}: allowlist still excuses {sorted(stale)}, which the CLI now exposes "
            f"or the SDK no longer accepts — delete those entries"
        )
        for param, reason in reasons.items():
            assert reason.strip(), f"{'.'.join(path)}.{param}: allowlisted with no reason"


# === hand-written composites =============================================================
#
# The checks above are parametrized over TABLE, so they see only the spec-driven commands.
# The composites in `onepin._cli.commands.composites` call the SDK directly and are invisible
# to every one of them -- including `workflows duplicate` and `workflows preview-run`, which
# were TABLE rows until they grew flags the table cannot express. `regen.yml` runs `tests/build`
# and nothing else, so without the checks below a regen that renames `duplicate_workflow`
# leaves the generated PR green and surfaces as an AttributeError in a user's terminal.
#
# Keyed by dotted SDK path, valued by the params the composite actually passes.
_COMPOSITE_CALLS: dict[str, frozenset[str]] = {
    "uploads.create": frozenset({"filename", "category", "workspace_id"}),
    "voices.get": frozenset({"voice_id", "workspace_id"}),
    "voices.preview": frozenset({"voice_id", "language", "model", "workspace_id"}),
    "workflows.download_run": frozenset({"workflow_id", "run_id", "workspace_id"}),
    "workflows.download_run_node": frozenset({"workflow_id", "run_id", "node_id", "workspace_id"}),
    "workflows.duplicate_workflow": frozenset({"workflow_id", "workspace_id"}),
    "workflows.get": frozenset({"workflow_id", "workspace_id"}),
    "workflows.patch_workflow": frozenset({"workflow_id", "workspace_id", "name", "definition"}),
    "workflows.preview_run": frozenset({"workflow_id", "workspace_id", "request_options"}),
    "workflows.runs.start": frozenset({"workflow_id", "workspace_id", "request_options"}),
    "workflows.runs.status": frozenset({"workflow_id", "run_id", "workspace_id"}),
}

# Same contract as _INTENTIONALLY_UNEXPOSED, keyed by dotted SDK path.
_COMPOSITE_UNEXPOSED: dict[str, dict[str, str]] = {
    "workflows.runs.start": {
        "request": (
            "Run-scoped overrides ride as request_options.additional_body_parameters instead: "
            "the generated WorkflowRunStartIn defaults both fields to None, so Fern would "
            "serialize the unset one as an explicit null (see composites._run_scoped_body)."
        ),
    },
    "workflows.preview_run": {
        "request": (
            "Built by the same composites._run_scoped_body as workflows.runs.start, so the "
            "estimate prices the byte-identical body the run will send."
        ),
    },
}


def _resolve_composite_method(dotted: str):
    return _resolve_method(OnePinClient(token="op_live_test"), dotted)


def _cli_reachable(dotted: str) -> set[str]:
    """Params of one SDK method reachable from anywhere in the CLI.

    A method can be shared: ``workflows.patch_workflow`` backs both the ``workflows update``
    TABLE row and two composites, so ``description`` is reachable even though no composite
    passes it. The union is the question the drift check actually asks -- "can a user set
    this at all" -- not "does this one call site set it".
    """
    reachable = set(_COMPOSITE_CALLS.get(dotted, frozenset()))
    for cmd in TABLE:
        paths = cmd.method_paths if isinstance(cmd.method_paths, tuple) else (cmd.method_paths,)
        if dotted in paths:
            reachable |= _exposed_dests(cmd)
    return reachable


@pytest.mark.parametrize("dotted", sorted(_COMPOSITE_CALLS), ids=lambda d: d)
def test_composite_method_resolves(dotted: str) -> None:
    """Every SDK method a composite calls still exists on a built client.

    This is `test_method_resolves` for the commands that are not TABLE rows. A rename in a
    regen fails here instead of at the moment a user runs the command.
    """
    assert callable(_resolve_composite_method(dotted)), f"{dotted} resolved to something not callable"


@pytest.mark.parametrize("dotted", sorted(_COMPOSITE_CALLS), ids=lambda d: d)
def test_composite_passed_params_are_accepted(dotted: str) -> None:
    """Every param a composite passes is one the SDK method still takes."""
    accepted = set(inspect.signature(_resolve_composite_method(dotted)).parameters)
    unknown = _COMPOSITE_CALLS[dotted] - accepted
    assert not unknown, (
        f"{dotted}: composites.py passes {sorted(unknown)}, which the method no longer accepts — "
        f"update the call site in composites.py and the entry in _COMPOSITE_CALLS"
    )


@pytest.mark.parametrize("dotted", sorted(_COMPOSITE_CALLS), ids=lambda d: d)
def test_no_unexposed_composite_sdk_params(dotted: str) -> None:
    """Reverse drift for the composites: a param the SDK gains must reach the CLI or be excused."""
    missing = _accepted_params(_resolve_composite_method(dotted)) - _cli_reachable(dotted)
    missing -= set(_COMPOSITE_UNEXPOSED.get(dotted, {}))

    assert not missing, (
        f"{dotted}: accepts {sorted(missing)} but no CLI flag reaches it. Either add the option "
        f"to the composite in commands/composites.py (and to _COMPOSITE_CALLS), or record the "
        f"decision in _COMPOSITE_UNEXPOSED with the reason."
    )


def test_composite_allowlist_has_no_stale_entries() -> None:
    """The composite allowlist may only name gaps that are still gaps."""
    for dotted, reasons in _COMPOSITE_UNEXPOSED.items():
        assert dotted in _COMPOSITE_CALLS, f"_COMPOSITE_UNEXPOSED names {dotted}, which is not in _COMPOSITE_CALLS"
        assert reasons, f"{dotted}: allowlist entry is empty — drop the key instead"
        gaps = _accepted_params(_resolve_composite_method(dotted)) - _cli_reachable(dotted)
        stale = set(reasons) - gaps
        assert not stale, (
            f"{dotted}: allowlist still excuses {sorted(stale)}, which the CLI now reaches or the "
            f"SDK no longer accepts — delete those entries"
        )
        for param, reason in reasons.items():
            assert reason.strip(), f"{dotted}.{param}: allowlisted with no reason"


def test_composite_calls_covers_every_sdk_call_site() -> None:
    """_COMPOSITE_CALLS must name every SDK method composites.py actually calls.

    A hand-maintained list silently stops covering the code it was written for. Reading the
    call sites out of the source keeps a newly added composite from slipping past the three
    checks above the same way `duplicate`/`preview-run` slipped past the TABLE ones.
    """
    import re
    from pathlib import Path

    import onepin._cli.commands.composites as composites_module

    source = Path(composites_module.__file__).read_text(encoding="utf-8")
    # `client.workflows.runs.start(` / `client.voices.get(`, and the bare-attribute form
    # `method = client.workflows.download_run` used where the method is picked then called.
    called = {match.group(1) for match in re.finditer(r"\bclient\.((?:[a-z_]+\.)+[a-z_]+)\b", source)}
    called = {path for path in called if not path.startswith("_")}

    missing = called - set(_COMPOSITE_CALLS)
    assert not missing, (
        f"composites.py calls {sorted(missing)} but _COMPOSITE_CALLS does not list it — add an "
        f"entry so the drift checks cover the new call site"
    )

    unused = set(_COMPOSITE_CALLS) - called
    assert not unused, f"_COMPOSITE_CALLS lists {sorted(unused)}, which composites.py no longer calls — drop it"
