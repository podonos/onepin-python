"""Paginate workflows and fetch a single one by id."""

import os

from onepin import OnePinClient


def main() -> None:
    client = OnePinClient(token=os.environ["ONEPIN_API_KEY"])

    # `list()` returns a SyncPager — iterate items directly, or use `.iter_pages()`.
    for index, workflow in enumerate(client.workflows.list()):
        print(workflow)
        if index >= 4:
            break

    # Fetch one workflow by id:
    # detail = client.workflows.get(workflow_id="wf_...")
    # print(detail)


if __name__ == "__main__":
    main()
