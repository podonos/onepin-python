"""Error handling, retries, and timeouts.

Any non-2xx response raises a subclass of `ApiError` exposing `.status_code` and `.body`.
Per-request behaviour is tuned via `request_options`; client-wide timeout via `timeout=`.
"""

import os

from onepin import OnePinClient
from onepin.core.api_error import ApiError


def main() -> None:
    client = OnePinClient(token=os.environ["ONEPIN_API_KEY"], timeout=20.0)

    try:
        client.workflows.get(
            workflow_id="wf_does_not_exist",
            request_options={"max_retries": 1, "timeout_in_seconds": 5},
        )
    except ApiError as error:
        print("API error:", error.status_code)
        print("body:", error.body)


if __name__ == "__main__":
    main()
