# Examples

Runnable snippets for the Onepin Python SDK. Each reads your API key from the
`ONEPIN_API_KEY` environment variable.

```sh
pip install onepin
export ONEPIN_API_KEY="op_..."        # create one at https://app.onepin.ai/workspace/~/settings/api
python examples/quickstart.py
```

| File | Shows |
|------|-------|
| `quickstart.py` | Construct a client, list workflows |
| `list_workflows.py` | Paginate workflows, fetch one by id |
| `async_client.py` | `AsyncOnePinClient` + async pagination |
| `error_handling.py` | `ApiError`, retries, timeouts |

By default the client targets **PROD** (`https://api.onepin.ai`). Pass
`environment=OnePinClientEnvironment.DEV` or `base_url="https://dev-api.onepin.ai"` to
target another host. See the repo [README](../README.md#sdk-usage) and the full
per-endpoint reference in [`src/onepin/reference.md`](../src/onepin/reference.md).
