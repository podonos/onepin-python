"""Fast-startup guarantee: importing the CLI must not pull in the Fern SDK.

``onepin --help`` / ``onepin login`` must stay snappy and never import the heavy generated
client. The dispatcher lazy-imports the SDK only inside synthesized command bodies.
"""

from __future__ import annotations

import subprocess
import sys


def test_importing_main_does_not_import_sdk_client() -> None:
    code = (
        "import sys, onepin._cli.main; "
        "assert 'onepin.client' not in sys.modules, 'onepin.client leaked'; "
        "assert 'onepin.workflows' not in sys.modules, 'onepin.workflows leaked'; "
        "print('ok')"
    )
    result = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    assert "ok" in result.stdout


def test_building_app_does_not_import_sdk_client() -> None:
    # Even constructing the full command tree (registry + manifest) stays SDK-free.
    code = (
        "import sys; "
        "import typer; "
        "from onepin._cli.main import app; "
        "typer.main.get_command(app); "
        "assert 'onepin.client' not in sys.modules, 'onepin.client leaked at build'; "
        "print('ok')"
    )
    result = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    assert "ok" in result.stdout
