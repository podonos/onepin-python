"""Contract test: every TABLE row must resolve against the real Fern SDK.

Auto-derived from :data:`onepin._cli._spec.TABLE`. For each command this asserts that:

- the dotted ``method`` path resolves to a callable on a built client,
- each positional arg and each forwarded option ``dest`` is a parameter the method accepts
  (or the method accepts ``**kwargs``), and
- every parameter the method marks *required* is supplied by the row (positional, option,
  or const).

This fails loudly if a Fern regen renames or drops a method/param the CLI depends on.
"""

from __future__ import annotations

import inspect
from typing import get_args

import pytest

from onepin._cli._dispatch import _resolve_method
from onepin._cli._spec import TABLE, Cmd
from onepin.client import OnePinClient
from onepin.types import NodeType

# Options whose dest is consumed by the CLI itself, not forwarded to the SDK.
_LOCAL_DESTS = {"json_output_local", "reveal", "yes"}
_LOCAL_FLAGS = {"--json", "--reveal", "--yes"}


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
