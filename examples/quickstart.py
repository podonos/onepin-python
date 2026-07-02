"""Quickstart: construct a client and make a few read calls.

Run:
    pip install onepin
    export ONEPIN_API_KEY="op_..."
    python examples/quickstart.py
"""

import os

from onepin import OnePinClient


def main() -> None:
    client = OnePinClient(token=os.environ["ONEPIN_API_KEY"])

    # Workflows in your workspace. `list()` returns a pager you can iterate directly.
    for workflow in client.workflows.list():
        print("workflow:", workflow)
        break  # just the first


if __name__ == "__main__":
    main()
