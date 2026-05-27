"""Verify py.typed marker survives wheel + sdist build."""

from __future__ import annotations

import subprocess
import sys
import tarfile
import zipfile
from pathlib import Path


def test_py_typed_in_wheel_and_sdist(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[2]
    dist_dir = tmp_path / "dist"
    subprocess.check_call(
        [sys.executable, "-m", "build", "--outdir", str(dist_dir)],
        cwd=repo_root,
    )
    wheels = list(dist_dir.glob("*.whl"))
    sdists = list(dist_dir.glob("*.tar.gz"))
    assert wheels, "no wheel produced"
    assert sdists, "no sdist produced"

    with zipfile.ZipFile(wheels[0]) as zf:
        names = zf.namelist()
    assert "onepin/py.typed" in names, f"py.typed missing from wheel; got: {sorted(names)[:10]}..."
    assert "onepin/_cli/py.typed" in names, "CLI py.typed missing from wheel"

    with tarfile.open(sdists[0]) as tf:
        names = tf.getnames()
    assert any(n.endswith("/onepin/py.typed") for n in names), "py.typed missing from sdist"
    assert any(n.endswith("/onepin/_cli/py.typed") for n in names), "CLI py.typed missing from sdist"
