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
        declared.append(opt.dest_name)
    declared.extend(cmd.consts.keys())

    if accepts_kwargs:
        return
    for name in declared:
        assert name in params, f"{cmd.method} does not accept declared param {name!r} (have {list(params)})"


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


def _unexposed_params(cmd: Cmd) -> set[str]:
    """SDK params this command accepts but offers no way to set.

    ``workspace_id`` is excluded when the method takes it *keyword-only*, which is the SDK's
    workspace-scoping convention: the dispatcher fills that from the global ``--workspace`` /
    ``ONEPIN_WORKSPACE_ID``, so it is reachable without a per-command flag. A method whose
    ``workspace_id`` is positional is a path parameter instead and gets no such pass.
    """
    method = _resolve_cmd_method(cmd)
    sig = inspect.signature(method)
    accepted = {
        name
        for name, param in sig.parameters.items()
        if param.kind not in (inspect.Parameter.VAR_KEYWORD, inspect.Parameter.VAR_POSITIONAL)
    } - _NEVER_A_FLAG
    if _accepts_workspace_kwarg(method):
        accepted.discard("workspace_id")
    return accepted - _exposed_dests(cmd)


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
