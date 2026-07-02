"""Cover the manifest + Markdown renderer in-process.

`_manifest` is the single source behind both `onepin schema` and the README drift gate.
The README-sync test exercises the renderer via a subprocess (coverage can't see it), so
these tests call `build_manifest` / `render_markdown` directly to exercise every branch:
group recursion, leaf description, positional args, subgroup bucketing, and help tails.
"""

from __future__ import annotations

from onepin._cli import _manifest


def test_build_manifest_shape() -> None:
    from onepin._cli.main import app

    manifest = _manifest.build_manifest(app)
    assert manifest["name"] == "onepin"
    commands = manifest["commands"]
    assert isinstance(commands, list) and len(commands) > 50

    # Sorted by path for stable snapshots.
    paths = [tuple(c["path"]) for c in commands]
    assert paths == sorted(paths)

    # Every entry has the contract keys.
    for entry in commands:
        assert {"path", "group", "name", "args", "options", "destructive"} <= entry.keys()

    # A destructive command with a positional arg is described correctly.
    delete = next(c for c in commands if c["path"] == ["workflows", "delete"])
    assert delete["destructive"] is True
    assert any(a["name"] == "workflow_id" for a in delete["args"])

    # An option carries flag/type/required/default/help; --help is filtered out.
    voices_list = next(c for c in commands if c["path"] == ["voices", "list"])
    flags = {o["flag"] for o in voices_list["options"]}
    assert "--help" not in flags and "--limit" in flags


def test_render_markdown_structure() -> None:
    md = _manifest.render_markdown()
    assert md.startswith("## CLI command reference")
    assert md.endswith("\n")

    # Top-level group heading and a nested subgroup heading (workflows runs).
    assert "### workflows" in md
    assert "#### workflows runs" in md

    # A command WITH a positional arg renders the <arg> form and a help tail (em dash).
    assert "- `onepin workflows show <workflow_id>` — " in md
    # A no-arg leaf command renders without angle brackets.
    assert "- `onepin templates list`" in md


def test_render_markdown_deterministic() -> None:
    assert _manifest.render_markdown() == _manifest.render_markdown()
