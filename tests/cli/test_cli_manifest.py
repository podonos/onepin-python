"""Snapshot test for the ``onepin schema`` manifest (the agent contract).

The manifest is the stable machine interface for agents. This test pins its shape so any
change to the command surface is a deliberate, reviewed snapshot update rather than a silent
contract drift. Regenerate with: ``UPDATE_SNAPSHOT=1 pytest tests/cli/test_cli_manifest.py``.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

from onepin._cli._manifest import build_manifest
from onepin._cli.main import app

_SNAPSHOT = Path(__file__).parent / "_manifest_snapshot.json"


def _normalize(manifest: dict) -> dict:
    # Version changes per build; pin everything except the version string.
    copy = dict(manifest)
    copy["version"] = "<version>"
    return copy


def test_manifest_matches_snapshot() -> None:
    manifest = _normalize(build_manifest(app))
    actual = json.dumps(manifest, indent=2, sort_keys=True)

    if os.environ.get("UPDATE_SNAPSHOT") or not _SNAPSHOT.exists():
        _SNAPSHOT.write_text(actual + "\n")

    expected = _SNAPSHOT.read_text().rstrip("\n")
    assert actual == expected, (
        "Manifest drifted from snapshot. If intentional, regenerate with "
        "UPDATE_SNAPSHOT=1 pytest tests/cli/test_cli_manifest.py"
    )


def test_manifest_shape() -> None:
    manifest = build_manifest(app)
    assert manifest["name"] == "onepin"
    assert isinstance(manifest["commands"], list)
    for cmd in manifest["commands"]:
        assert set(cmd) == {"path", "group", "name", "args", "options", "destructive"}
        assert isinstance(cmd["args"], list)
        assert isinstance(cmd["options"], list)
        assert isinstance(cmd["destructive"], bool)


def test_destructive_commands_flagged() -> None:
    manifest = build_manifest(app)
    by_path = {tuple(c["path"]): c for c in manifest["commands"]}
    assert by_path[("workflows", "delete")]["destructive"] is True
    assert by_path[("workflows", "runs", "cancel")]["destructive"] is True
    assert by_path[("workflows", "show")]["destructive"] is False
