# Reference
## health
<details><summary><code>client.health.<a href="src/onepin/health/client.py">liveness</a>() -> typing.Any</code></summary>
<dl>
<dd>

#### 📝 Description

<dl>
<dd>

<dl>
<dd>

Liveness probe — always returns 200.
</dd>
</dl>
</dd>
</dl>

#### 🔌 Usage

<dl>
<dd>

<dl>
<dd>

```python
from onepin import OnePinClient
from onepin.environment import OnePinClientEnvironment

client = OnePinClient(
    token="<token>",
    environment=OnePinClientEnvironment.PROD,
)

client.health.liveness()

```
</dd>
</dl>
</dd>
</dl>

#### ⚙️ Parameters

<dl>
<dd>

<dl>
<dd>

**request_options:** `typing.Optional[RequestOptions]` — Request-specific configuration.
    
</dd>
</dl>
</dd>
</dl>


</dd>
</dl>
</details>

<details><summary><code>client.health.<a href="src/onepin/health/client.py">readiness</a>() -> typing.Any</code></summary>
<dl>
<dd>

#### 📝 Description

<dl>
<dd>

<dl>
<dd>

Readiness probe — checks DB and Redis connectivity.
</dd>
</dl>
</dd>
</dl>

#### 🔌 Usage

<dl>
<dd>

<dl>
<dd>

```python
from onepin import OnePinClient
from onepin.environment import OnePinClientEnvironment

client = OnePinClient(
    token="<token>",
    environment=OnePinClientEnvironment.PROD,
)

client.health.readiness()

```
</dd>
</dl>
</dd>
</dl>

#### ⚙️ Parameters

<dl>
<dd>

<dl>
<dd>

**request_options:** `typing.Optional[RequestOptions]` — Request-specific configuration.
    
</dd>
</dl>
</dd>
</dl>


</dd>
</dl>
</details>

## webhooks
<details><summary><code>client.webhooks.<a href="src/onepin/webhooks/client.py">clerk_webhook</a>() -> ApiResponseDict</code></summary>
<dl>
<dd>

#### 📝 Description

<dl>
<dd>

<dl>
<dd>

Handle Clerk webhook events. Verifies svix signature.
</dd>
</dl>
</dd>
</dl>

#### 🔌 Usage

<dl>
<dd>

<dl>
<dd>

```python
from onepin import OnePinClient
from onepin.environment import OnePinClientEnvironment

client = OnePinClient(
    token="<token>",
    environment=OnePinClientEnvironment.PROD,
)

client.webhooks.clerk_webhook()

```
</dd>
</dl>
</dd>
</dl>

#### ⚙️ Parameters

<dl>
<dd>

<dl>
<dd>

**request_options:** `typing.Optional[RequestOptions]` — Request-specific configuration.
    
</dd>
</dl>
</dd>
</dl>


</dd>
</dl>
</details>

<details><summary><code>client.webhooks.<a href="src/onepin/webhooks/client.py">stripe_webhook</a>() -> ApiResponseDict</code></summary>
<dl>
<dd>

#### 📝 Description

<dl>
<dd>

<dl>
<dd>

Handle Stripe webhook events. Verifies Stripe-Signature header.
</dd>
</dl>
</dd>
</dl>

#### 🔌 Usage

<dl>
<dd>

<dl>
<dd>

```python
from onepin import OnePinClient
from onepin.environment import OnePinClientEnvironment

client = OnePinClient(
    token="<token>",
    environment=OnePinClientEnvironment.PROD,
)

client.webhooks.stripe_webhook()

```
</dd>
</dl>
</dd>
</dl>

#### ⚙️ Parameters

<dl>
<dd>

<dl>
<dd>

**request_options:** `typing.Optional[RequestOptions]` — Request-specific configuration.
    
</dd>
</dl>
</dd>
</dl>


</dd>
</dl>
</details>

## auth
<details><summary><code>client.auth.<a href="src/onepin/auth/client.py">whoami</a>() -> ApiResponseAuthWhoamiOut</code></summary>
<dl>
<dd>

#### 📝 Description

<dl>
<dd>

<dl>
<dd>

Return the resolved Clerk or API-key authentication context.
</dd>
</dl>
</dd>
</dl>

#### 🔌 Usage

<dl>
<dd>

<dl>
<dd>

```python
from onepin import OnePinClient
from onepin.environment import OnePinClientEnvironment

client = OnePinClient(
    token="<token>",
    environment=OnePinClientEnvironment.PROD,
)

client.auth.whoami()

```
</dd>
</dl>
</dd>
</dl>

#### ⚙️ Parameters

<dl>
<dd>

<dl>
<dd>

**request_options:** `typing.Optional[RequestOptions]` — Request-specific configuration.
    
</dd>
</dl>
</dd>
</dl>


</dd>
</dl>
</details>

## api-keys
<details><summary><code>client.api_keys.<a href="src/onepin/api_keys/client.py">list_api_keys</a>(...) -> ApiCountedListResponseApiKeyOut</code></summary>
<dl>
<dd>

#### 📝 Description

<dl>
<dd>

<dl>
<dd>

List API keys for the current workspace without secret material.
</dd>
</dl>
</dd>
</dl>

#### 🔌 Usage

<dl>
<dd>

<dl>
<dd>

```python
from onepin import OnePinClient
from onepin.environment import OnePinClientEnvironment

client = OnePinClient(
    token="<token>",
    environment=OnePinClientEnvironment.PROD,
)

client.api_keys.list_api_keys()

```
</dd>
</dl>
</dd>
</dl>

#### ⚙️ Parameters

<dl>
<dd>

<dl>
<dd>

**offset:** `typing.Optional[int]` 
    
</dd>
</dl>

<dl>
<dd>

**limit:** `typing.Optional[int]` 
    
</dd>
</dl>

<dl>
<dd>

**status:** `typing.Optional[ApiKeyListStatus]` — API-key list status filter. Defaults to currently usable keys. `revoked` returns unavailable keys (`active=false` or `revoked_at` is set); `all` returns all workspace API-key metadata rows.
    
</dd>
</dl>

<dl>
<dd>

**workspace_id:** `typing.Optional[str]` 
    
</dd>
</dl>

<dl>
<dd>

**request_options:** `typing.Optional[RequestOptions]` — Request-specific configuration.
    
</dd>
</dl>
</dd>
</dl>


</dd>
</dl>
</details>

<details><summary><code>client.api_keys.<a href="src/onepin/api_keys/client.py">create_api_key</a>(...) -> ApiResponseApiKeyCreatedOut</code></summary>
<dl>
<dd>

#### 📝 Description

<dl>
<dd>

<dl>
<dd>

Create a live API key and return its plaintext value exactly once.
</dd>
</dl>
</dd>
</dl>

#### 🔌 Usage

<dl>
<dd>

<dl>
<dd>

```python
from onepin import OnePinClient
from onepin.environment import OnePinClientEnvironment

client = OnePinClient(
    token="<token>",
    environment=OnePinClientEnvironment.PROD,
)

client.api_keys.create_api_key(
    name="name",
)

```
</dd>
</dl>
</dd>
</dl>

#### ⚙️ Parameters

<dl>
<dd>

<dl>
<dd>

**name:** `str` 
    
</dd>
</dl>

<dl>
<dd>

**workspace_id:** `typing.Optional[str]` 
    
</dd>
</dl>

<dl>
<dd>

**scopes:** `typing.Optional[typing.List[ApiKeyScope]]` 
    
</dd>
</dl>

<dl>
<dd>

**rate_limit_per_min:** `typing.Optional[int]` 
    
</dd>
</dl>

<dl>
<dd>

**key_type:** `typing.Optional[str]` — Phase 1 supports live bearer keys only; test/public are reserved.
    
</dd>
</dl>

<dl>
<dd>

**request_options:** `typing.Optional[RequestOptions]` — Request-specific configuration.
    
</dd>
</dl>
</dd>
</dl>


</dd>
</dl>
</details>

<details><summary><code>client.api_keys.<a href="src/onepin/api_keys/client.py">get_api_key</a>(...) -> ApiResponseApiKeyOut</code></summary>
<dl>
<dd>

#### 📝 Description

<dl>
<dd>

<dl>
<dd>

Get one API-key metadata record for the current workspace.
</dd>
</dl>
</dd>
</dl>

#### 🔌 Usage

<dl>
<dd>

<dl>
<dd>

```python
from onepin import OnePinClient
from onepin.environment import OnePinClientEnvironment

client = OnePinClient(
    token="<token>",
    environment=OnePinClientEnvironment.PROD,
)

client.api_keys.get_api_key(
    key_id="key_id",
)

```
</dd>
</dl>
</dd>
</dl>

#### ⚙️ Parameters

<dl>
<dd>

<dl>
<dd>

**key_id:** `str` 
    
</dd>
</dl>

<dl>
<dd>

**workspace_id:** `typing.Optional[str]` 
    
</dd>
</dl>

<dl>
<dd>

**request_options:** `typing.Optional[RequestOptions]` — Request-specific configuration.
    
</dd>
</dl>
</dd>
</dl>


</dd>
</dl>
</details>

<details><summary><code>client.api_keys.<a href="src/onepin/api_keys/client.py">delete_api_key</a>(...) -> ApiResponseApiKeyOut</code></summary>
<dl>
<dd>

#### 📝 Description

<dl>
<dd>

<dl>
<dd>

Soft-revoke an API key for the current workspace.
</dd>
</dl>
</dd>
</dl>

#### 🔌 Usage

<dl>
<dd>

<dl>
<dd>

```python
from onepin import OnePinClient
from onepin.environment import OnePinClientEnvironment

client = OnePinClient(
    token="<token>",
    environment=OnePinClientEnvironment.PROD,
)

client.api_keys.delete_api_key(
    key_id="key_id",
)

```
</dd>
</dl>
</dd>
</dl>

#### ⚙️ Parameters

<dl>
<dd>

<dl>
<dd>

**key_id:** `str` 
    
</dd>
</dl>

<dl>
<dd>

**workspace_id:** `typing.Optional[str]` 
    
</dd>
</dl>

<dl>
<dd>

**request_options:** `typing.Optional[RequestOptions]` — Request-specific configuration.
    
</dd>
</dl>
</dd>
</dl>


</dd>
</dl>
</details>

<details><summary><code>client.api_keys.<a href="src/onepin/api_keys/client.py">update_api_key</a>(...) -> ApiResponseApiKeyOut</code></summary>
<dl>
<dd>

#### 📝 Description

<dl>
<dd>

<dl>
<dd>

Update API-key metadata, scopes, rate limit, or active state.
</dd>
</dl>
</dd>
</dl>

#### 🔌 Usage

<dl>
<dd>

<dl>
<dd>

```python
from onepin import OnePinClient
from onepin.environment import OnePinClientEnvironment

client = OnePinClient(
    token="<token>",
    environment=OnePinClientEnvironment.PROD,
)

client.api_keys.update_api_key(
    key_id="key_id",
)

```
</dd>
</dl>
</dd>
</dl>

#### ⚙️ Parameters

<dl>
<dd>

<dl>
<dd>

**key_id:** `str` 
    
</dd>
</dl>

<dl>
<dd>

**workspace_id:** `typing.Optional[str]` 
    
</dd>
</dl>

<dl>
<dd>

**name:** `typing.Optional[str]` 
    
</dd>
</dl>

<dl>
<dd>

**scopes:** `typing.Optional[typing.List[ApiKeyScope]]` 
    
</dd>
</dl>

<dl>
<dd>

**rate_limit_per_min:** `typing.Optional[int]` 
    
</dd>
</dl>

<dl>
<dd>

**active:** `typing.Optional[bool]` 
    
</dd>
</dl>

<dl>
<dd>

**request_options:** `typing.Optional[RequestOptions]` — Request-specific configuration.
    
</dd>
</dl>
</dd>
</dl>


</dd>
</dl>
</details>

<details><summary><code>client.api_keys.<a href="src/onepin/api_keys/client.py">rotate_api_key</a>(...) -> ApiResponseApiKeyRotateOut</code></summary>
<dl>
<dd>

#### 📝 Description

<dl>
<dd>

<dl>
<dd>

Rotate an API key by revoking the old row and creating a new key.
</dd>
</dl>
</dd>
</dl>

#### 🔌 Usage

<dl>
<dd>

<dl>
<dd>

```python
from onepin import OnePinClient
from onepin.environment import OnePinClientEnvironment

client = OnePinClient(
    token="<token>",
    environment=OnePinClientEnvironment.PROD,
)

client.api_keys.rotate_api_key(
    key_id="key_id",
)

```
</dd>
</dl>
</dd>
</dl>

#### ⚙️ Parameters

<dl>
<dd>

<dl>
<dd>

**key_id:** `str` 
    
</dd>
</dl>

<dl>
<dd>

**workspace_id:** `typing.Optional[str]` 
    
</dd>
</dl>

<dl>
<dd>

**request_options:** `typing.Optional[RequestOptions]` — Request-specific configuration.
    
</dd>
</dl>
</dd>
</dl>


</dd>
</dl>
</details>

## dictionary
<details><summary><code>client.dictionary.<a href="src/onepin/dictionary/client.py">list_dictionary_entries</a>(...) -> ApiListResponseDictionaryOut</code></summary>
<dl>
<dd>

#### 📝 Description

<dl>
<dd>

<dl>
<dd>

List dictionary entries for a single language in the current workspace.
</dd>
</dl>
</dd>
</dl>

#### 🔌 Usage

<dl>
<dd>

<dl>
<dd>

```python
from onepin import OnePinClient
from onepin.environment import OnePinClientEnvironment

client = OnePinClient(
    token="<token>",
    environment=OnePinClientEnvironment.PROD,
)

client.dictionary.list_dictionary_entries(
    language="de-de",
)

```
</dd>
</dl>
</dd>
</dl>

#### ⚙️ Parameters

<dl>
<dd>

<dl>
<dd>

**language:** `ListDictionaryEntriesApiV1DictionaryGetRequestLanguage` — BCP-47 language code, e.g. en-us, ko-kr
    
</dd>
</dl>

<dl>
<dd>

**method:** `typing.Optional[typing.List[DictionaryMethod]]` — Repeat for OR, e.g. ?method=spelled&method=recorded
    
</dd>
</dl>

<dl>
<dd>

**sort:** `typing.Optional[ListDictionaryEntriesApiV1DictionaryGetRequestSort]` 
    
</dd>
</dl>

<dl>
<dd>

**order:** `typing.Optional[ListDictionaryEntriesApiV1DictionaryGetRequestOrder]` 
    
</dd>
</dl>

<dl>
<dd>

**offset:** `typing.Optional[int]` 
    
</dd>
</dl>

<dl>
<dd>

**limit:** `typing.Optional[int]` 
    
</dd>
</dl>

<dl>
<dd>

**workspace_id:** `typing.Optional[str]` 
    
</dd>
</dl>

<dl>
<dd>

**request_options:** `typing.Optional[RequestOptions]` — Request-specific configuration.
    
</dd>
</dl>
</dd>
</dl>


</dd>
</dl>
</details>

<details><summary><code>client.dictionary.<a href="src/onepin/dictionary/client.py">create_dictionary_entry</a>(...) -> ApiResponseDictionaryOut</code></summary>
<dl>
<dd>

#### 📝 Description

<dl>
<dd>

<dl>
<dd>

Create a new dictionary entry in the current workspace.
</dd>
</dl>
</dd>
</dl>

#### 🔌 Usage

<dl>
<dd>

<dl>
<dd>

```python
from onepin import OnePinClient
from onepin.environment import OnePinClientEnvironment

client = OnePinClient(
    token="<token>",
    environment=OnePinClientEnvironment.PROD,
)

client.dictionary.create_dictionary_entry(
    word="word",
    method="spelled",
    language="language",
)

```
</dd>
</dl>
</dd>
</dl>

#### ⚙️ Parameters

<dl>
<dd>

<dl>
<dd>

**word:** `str` 
    
</dd>
</dl>

<dl>
<dd>

**method:** `DictionaryMethod` 
    
</dd>
</dl>

<dl>
<dd>

**language:** `str` 
    
</dd>
</dl>

<dl>
<dd>

**workspace_id:** `typing.Optional[str]` 
    
</dd>
</dl>

<dl>
<dd>

**description:** `typing.Optional[str]` 
    
</dd>
</dl>

<dl>
<dd>

**pronunciation:** `typing.Optional[str]` 
    
</dd>
</dl>

<dl>
<dd>

**upload_id:** `typing.Optional[str]` 
    
</dd>
</dl>

<dl>
<dd>

**ipa:** `typing.Optional[str]` — User-provided IPA transcription. Persisted as-is. Auto-generation via phonemizer/LLM is a POD-256 follow-up.
    
</dd>
</dl>

<dl>
<dd>

**request_options:** `typing.Optional[RequestOptions]` — Request-specific configuration.
    
</dd>
</dl>
</dd>
</dl>


</dd>
</dl>
</details>

<details><summary><code>client.dictionary.<a href="src/onepin/dictionary/client.py">search_dictionary_entries</a>(...) -> ApiListResponseDictionaryOut</code></summary>
<dl>
<dd>

#### 📝 Description

<dl>
<dd>

<dl>
<dd>

Cross-language search over dictionary entries.
</dd>
</dl>
</dd>
</dl>

#### 🔌 Usage

<dl>
<dd>

<dl>
<dd>

```python
from onepin import OnePinClient
from onepin.environment import OnePinClientEnvironment

client = OnePinClient(
    token="<token>",
    environment=OnePinClientEnvironment.PROD,
)

client.dictionary.search_dictionary_entries(
    search="search",
)

```
</dd>
</dl>
</dd>
</dl>

#### ⚙️ Parameters

<dl>
<dd>

<dl>
<dd>

**search:** `str` 
    
</dd>
</dl>

<dl>
<dd>

**sort:** `typing.Optional[SearchDictionaryEntriesApiV1DictionarySearchGetRequestSort]` 
    
</dd>
</dl>

<dl>
<dd>

**order:** `typing.Optional[SearchDictionaryEntriesApiV1DictionarySearchGetRequestOrder]` 
    
</dd>
</dl>

<dl>
<dd>

**offset:** `typing.Optional[int]` 
    
</dd>
</dl>

<dl>
<dd>

**limit:** `typing.Optional[int]` 
    
</dd>
</dl>

<dl>
<dd>

**language:** `typing.Optional[typing.List[SearchDictionaryEntriesApiV1DictionarySearchGetRequestLanguageItem]]` — Repeat for OR, e.g. ?language=en-us&language=ko-kr
    
</dd>
</dl>

<dl>
<dd>

**workspace_id:** `typing.Optional[str]` 
    
</dd>
</dl>

<dl>
<dd>

**request_options:** `typing.Optional[RequestOptions]` — Request-specific configuration.
    
</dd>
</dl>
</dd>
</dl>


</dd>
</dl>
</details>

<details><summary><code>client.dictionary.<a href="src/onepin/dictionary/client.py">list_dictionary_languages</a>(...) -> ApiResponseListDictionaryLanguageOut</code></summary>
<dl>
<dd>

#### 📝 Description

<dl>
<dd>

<dl>
<dd>

Return distinct languages with entry counts, ordered by count DESC, code ASC.
</dd>
</dl>
</dd>
</dl>

#### 🔌 Usage

<dl>
<dd>

<dl>
<dd>

```python
from onepin import OnePinClient
from onepin.environment import OnePinClientEnvironment

client = OnePinClient(
    token="<token>",
    environment=OnePinClientEnvironment.PROD,
)

client.dictionary.list_dictionary_languages()

```
</dd>
</dl>
</dd>
</dl>

#### ⚙️ Parameters

<dl>
<dd>

<dl>
<dd>

**workspace_id:** `typing.Optional[str]` 
    
</dd>
</dl>

<dl>
<dd>

**request_options:** `typing.Optional[RequestOptions]` — Request-specific configuration.
    
</dd>
</dl>
</dd>
</dl>


</dd>
</dl>
</details>

<details><summary><code>client.dictionary.<a href="src/onepin/dictionary/client.py">suggest_pronunciation</a>(...) -> ApiResponsePronunciationSuggestion</code></summary>
<dl>
<dd>

#### 📝 Description

<dl>
<dd>

<dl>
<dd>

Return a deterministic FE-parity pronunciation fallback.

``language`` is reserved for future per-locale rules; ``ipa`` is reserved
for a future generator and is always ``None`` in this version.

Workspace scoping is enforced via ``get_current_workspace`` even though the
response is workspace-independent today: this keeps all ``/api/v1/``
endpoints uniform (see CLAUDE.md §Workspace Scoping) and leaves room for
per-workspace dictionary overrides when the generator lands.
</dd>
</dl>
</dd>
</dl>

#### 🔌 Usage

<dl>
<dd>

<dl>
<dd>

```python
from onepin import OnePinClient
from onepin.environment import OnePinClientEnvironment

client = OnePinClient(
    token="<token>",
    environment=OnePinClientEnvironment.PROD,
)

client.dictionary.suggest_pronunciation(
    word="word",
    language="language",
)

```
</dd>
</dl>
</dd>
</dl>

#### ⚙️ Parameters

<dl>
<dd>

<dl>
<dd>

**word:** `str` 
    
</dd>
</dl>

<dl>
<dd>

**language:** `str` 
    
</dd>
</dl>

<dl>
<dd>

**workspace_id:** `typing.Optional[str]` 
    
</dd>
</dl>

<dl>
<dd>

**request_options:** `typing.Optional[RequestOptions]` — Request-specific configuration.
    
</dd>
</dl>
</dd>
</dl>


</dd>
</dl>
</details>

<details><summary><code>client.dictionary.<a href="src/onepin/dictionary/client.py">update_dictionary_entry</a>(...) -> ApiResponseDictionaryOut</code></summary>
<dl>
<dd>

#### 📝 Description

<dl>
<dd>

<dl>
<dd>

Update a dictionary entry scoped to the current workspace.
</dd>
</dl>
</dd>
</dl>

#### 🔌 Usage

<dl>
<dd>

<dl>
<dd>

```python
from onepin import OnePinClient
from onepin.environment import OnePinClientEnvironment

client = OnePinClient(
    token="<token>",
    environment=OnePinClientEnvironment.PROD,
)

client.dictionary.update_dictionary_entry(
    entry_id="entry_id",
)

```
</dd>
</dl>
</dd>
</dl>

#### ⚙️ Parameters

<dl>
<dd>

<dl>
<dd>

**entry_id:** `str` 
    
</dd>
</dl>

<dl>
<dd>

**workspace_id:** `typing.Optional[str]` 
    
</dd>
</dl>

<dl>
<dd>

**word:** `typing.Optional[str]` 
    
</dd>
</dl>

<dl>
<dd>

**description:** `typing.Optional[str]` 
    
</dd>
</dl>

<dl>
<dd>

**pronunciation:** `typing.Optional[str]` 
    
</dd>
</dl>

<dl>
<dd>

**upload_id:** `typing.Optional[str]` 
    
</dd>
</dl>

<dl>
<dd>

**method:** `typing.Optional[DictionaryMethod]` 
    
</dd>
</dl>

<dl>
<dd>

**language:** `typing.Optional[str]` 
    
</dd>
</dl>

<dl>
<dd>

**ipa:** `typing.Optional[str]` — User-provided IPA transcription. Persisted as-is. Auto-generation via phonemizer/LLM is a POD-256 follow-up.
    
</dd>
</dl>

<dl>
<dd>

**request_options:** `typing.Optional[RequestOptions]` — Request-specific configuration.
    
</dd>
</dl>
</dd>
</dl>


</dd>
</dl>
</details>

<details><summary><code>client.dictionary.<a href="src/onepin/dictionary/client.py">delete_dictionary_entry</a>(...) -> ApiResponseDict</code></summary>
<dl>
<dd>

#### 📝 Description

<dl>
<dd>

<dl>
<dd>

Soft-delete a dictionary entry scoped to the current workspace.
</dd>
</dl>
</dd>
</dl>

#### 🔌 Usage

<dl>
<dd>

<dl>
<dd>

```python
from onepin import OnePinClient
from onepin.environment import OnePinClientEnvironment

client = OnePinClient(
    token="<token>",
    environment=OnePinClientEnvironment.PROD,
)

client.dictionary.delete_dictionary_entry(
    entry_id="entry_id",
)

```
</dd>
</dl>
</dd>
</dl>

#### ⚙️ Parameters

<dl>
<dd>

<dl>
<dd>

**entry_id:** `str` 
    
</dd>
</dl>

<dl>
<dd>

**workspace_id:** `typing.Optional[str]` 
    
</dd>
</dl>

<dl>
<dd>

**request_options:** `typing.Optional[RequestOptions]` — Request-specific configuration.
    
</dd>
</dl>
</dd>
</dl>


</dd>
</dl>
</details>

## nodes
<details><summary><code>client.nodes.<a href="src/onepin/nodes/client.py">list_nodes</a>() -> ApiListResponseNodePortsOut</code></summary>
<dl>
<dd>

#### 📝 Description

<dl>
<dd>

<dl>
<dd>

List all node types and their input/output port definitions.
</dd>
</dl>
</dd>
</dl>

#### 🔌 Usage

<dl>
<dd>

<dl>
<dd>

```python
from onepin import OnePinClient
from onepin.environment import OnePinClientEnvironment

client = OnePinClient(
    token="<token>",
    environment=OnePinClientEnvironment.PROD,
)

client.nodes.list_nodes()

```
</dd>
</dl>
</dd>
</dl>

#### ⚙️ Parameters

<dl>
<dd>

<dl>
<dd>

**request_options:** `typing.Optional[RequestOptions]` — Request-specific configuration.
    
</dd>
</dl>
</dd>
</dl>


</dd>
</dl>
</details>

<details><summary><code>client.nodes.<a href="src/onepin/nodes/client.py">get_node_detail</a>(...) -> ApiResponseNodeDetailOut</code></summary>
<dl>
<dd>

#### 📝 Description

<dl>
<dd>

<dl>
<dd>

Return full node definition + runtime options for the canvas node-config UI.

Unlike `GET /nodes` (which returns only port schemas), this endpoint returns the
actual runtime values a user picks: available target languages (from settings),
the TTS model catalog grouped by provider, and a HATEOAS link to the workspace-
scoped voices list. Requires `X-Workspace-Id` for a uniform FE contract.
</dd>
</dl>
</dd>
</dl>

#### 🔌 Usage

<dl>
<dd>

<dl>
<dd>

```python
from onepin import OnePinClient
from onepin.environment import OnePinClientEnvironment

client = OnePinClient(
    token="<token>",
    environment=OnePinClientEnvironment.PROD,
)

client.nodes.get_node_detail(
    node_type="node_type",
)

```
</dd>
</dl>
</dd>
</dl>

#### ⚙️ Parameters

<dl>
<dd>

<dl>
<dd>

**node_type:** `str` 
    
</dd>
</dl>

<dl>
<dd>

**workspace_id:** `typing.Optional[str]` 
    
</dd>
</dl>

<dl>
<dd>

**request_options:** `typing.Optional[RequestOptions]` — Request-specific configuration.
    
</dd>
</dl>
</dd>
</dl>


</dd>
</dl>
</details>

## provider-keys
<details><summary><code>client.provider_keys.<a href="src/onepin/provider_keys/client.py">list_provider_keys</a>(...) -> ApiResponseProviderKeysManifestOut</code></summary>
<dl>
<dd>

#### 📝 Description

<dl>
<dd>

<dl>
<dd>

List BYOK provider-key schemas and status for the current workspace.
</dd>
</dl>
</dd>
</dl>

#### 🔌 Usage

<dl>
<dd>

<dl>
<dd>

```python
from onepin import OnePinClient
from onepin.environment import OnePinClientEnvironment

client = OnePinClient(
    token="<token>",
    environment=OnePinClientEnvironment.PROD,
)

client.provider_keys.list_provider_keys()

```
</dd>
</dl>
</dd>
</dl>

#### ⚙️ Parameters

<dl>
<dd>

<dl>
<dd>

**workspace_id:** `typing.Optional[str]` 
    
</dd>
</dl>

<dl>
<dd>

**request_options:** `typing.Optional[RequestOptions]` — Request-specific configuration.
    
</dd>
</dl>
</dd>
</dl>


</dd>
</dl>
</details>

<details><summary><code>client.provider_keys.<a href="src/onepin/provider_keys/client.py">put_provider_key</a>(...) -> ApiResponseProviderKeyItemOut</code></summary>
<dl>
<dd>

#### 📝 Description

<dl>
<dd>

<dl>
<dd>

Create or replace a BYOK provider key for the current workspace.

POD-301: gated by `byok_enabled` feature flag on the workspace owner's plan.
Free plan rejects with 403 FEATURE_NOT_IN_PLAN.
</dd>
</dl>
</dd>
</dl>

#### 🔌 Usage

<dl>
<dd>

<dl>
<dd>

```python
from onepin import OnePinClient
from onepin.environment import OnePinClientEnvironment

client = OnePinClient(
    token="<token>",
    environment=OnePinClientEnvironment.PROD,
)

client.provider_keys.put_provider_key(
    provider="elevenlabs",
    request={
        "key": "value"
    },
)

```
</dd>
</dl>
</dd>
</dl>

#### ⚙️ Parameters

<dl>
<dd>

<dl>
<dd>

**provider:** `ProviderKeyProvider` 
    
</dd>
</dl>

<dl>
<dd>

**request:** `typing.Dict[str, typing.Any]` — Provider-specific credential payload. The provider is the path parameter and must not be in body. Use GET /provider-keys data.providers[].credentials_schema for the matching provider as the canonical request schema.
    
</dd>
</dl>

<dl>
<dd>

**workspace_id:** `typing.Optional[str]` 
    
</dd>
</dl>

<dl>
<dd>

**request_options:** `typing.Optional[RequestOptions]` — Request-specific configuration.
    
</dd>
</dl>
</dd>
</dl>


</dd>
</dl>
</details>

<details><summary><code>client.provider_keys.<a href="src/onepin/provider_keys/client.py">delete_provider_key</a>(...) -> ApiResponseProviderKeyItemOut</code></summary>
<dl>
<dd>

#### 📝 Description

<dl>
<dd>

<dl>
<dd>

Delete a BYOK provider key for the current workspace idempotently.
</dd>
</dl>
</dd>
</dl>

#### 🔌 Usage

<dl>
<dd>

<dl>
<dd>

```python
from onepin import OnePinClient
from onepin.environment import OnePinClientEnvironment

client = OnePinClient(
    token="<token>",
    environment=OnePinClientEnvironment.PROD,
)

client.provider_keys.delete_provider_key(
    provider="elevenlabs",
)

```
</dd>
</dl>
</dd>
</dl>

#### ⚙️ Parameters

<dl>
<dd>

<dl>
<dd>

**provider:** `ProviderKeyProvider` 
    
</dd>
</dl>

<dl>
<dd>

**workspace_id:** `typing.Optional[str]` 
    
</dd>
</dl>

<dl>
<dd>

**request_options:** `typing.Optional[RequestOptions]` — Request-specific configuration.
    
</dd>
</dl>
</dd>
</dl>


</dd>
</dl>
</details>

## templates
<details><summary><code>client.templates.<a href="src/onepin/templates/client.py">list</a>(...) -> ApiListResponseTemplateOut</code></summary>
<dl>
<dd>

#### 📝 Description

<dl>
<dd>

<dl>
<dd>

List live published templates across workspaces (gallery).

Authenticated but not workspace-scoped — the gallery is cross-workspace
by design (published rows from any workspace). Does not require
`X-Workspace-Id`, so a freshly signed-up user without a workspace can
still browse templates.

Dual-auth: Clerk JWT or `op_live_*` API key (scope `templates:read`).
</dd>
</dl>
</dd>
</dl>

#### 🔌 Usage

<dl>
<dd>

<dl>
<dd>

```python
from onepin import OnePinClient
from onepin.environment import OnePinClientEnvironment

client = OnePinClient(
    token="<token>",
    environment=OnePinClientEnvironment.PROD,
)

client.templates.list()

```
</dd>
</dl>
</dd>
</dl>

#### ⚙️ Parameters

<dl>
<dd>

<dl>
<dd>

**category:** `typing.Optional[typing.List[TemplateCategory]]` — Repeat for OR, e.g. ?category=media&category=creative
    
</dd>
</dl>

<dl>
<dd>

**search:** `typing.Optional[str]` 
    
</dd>
</dl>

<dl>
<dd>

**sort:** `typing.Optional[ListTemplatesRequestSort]` 
    
</dd>
</dl>

<dl>
<dd>

**offset:** `typing.Optional[int]` 
    
</dd>
</dl>

<dl>
<dd>

**limit:** `typing.Optional[int]` 
    
</dd>
</dl>

<dl>
<dd>

**favorites_only:** `typing.Optional[bool]` 
    
</dd>
</dl>

<dl>
<dd>

**request_options:** `typing.Optional[RequestOptions]` — Request-specific configuration.
    
</dd>
</dl>
</dd>
</dl>


</dd>
</dl>
</details>

<details><summary><code>client.templates.<a href="src/onepin/templates/client.py">create_template</a>(...) -> ApiResponseTemplateOut</code></summary>
<dl>
<dd>

#### 📝 Description

<dl>
<dd>

<dl>
<dd>

Create a new workflow template in the current workspace.

The caller supplies a full `WorkflowDefinition` (graph + execution).
Save-time validation (`validate_definition_save`) mirrors the
`/api/v1/workflows` contract — duplicate node/edge IDs, port mismatches,
and other structural errors fail at write time rather than surfacing
when a caller later clones the template into a workflow.
</dd>
</dl>
</dd>
</dl>

#### 🔌 Usage

<dl>
<dd>

<dl>
<dd>

```python
from onepin import OnePinClient
from onepin.environment import OnePinClientEnvironment

client = OnePinClient(
    token="<token>",
    environment=OnePinClientEnvironment.PROD,
)

client.templates.create_template(
    name="name",
)

```
</dd>
</dl>
</dd>
</dl>

#### ⚙️ Parameters

<dl>
<dd>

<dl>
<dd>

**name:** `str` 
    
</dd>
</dl>

<dl>
<dd>

**workspace_id:** `typing.Optional[str]` 
    
</dd>
</dl>

<dl>
<dd>

**description:** `typing.Optional[str]` 
    
</dd>
</dl>

<dl>
<dd>

**category:** `typing.Optional[TemplateCategory]` 
    
</dd>
</dl>

<dl>
<dd>

**definition:** `typing.Optional[WorkflowDefinitionInput]` 
    
</dd>
</dl>

<dl>
<dd>

**request_options:** `typing.Optional[RequestOptions]` — Request-specific configuration.
    
</dd>
</dl>
</dd>
</dl>


</dd>
</dl>
</details>

<details><summary><code>client.templates.<a href="src/onepin/templates/client.py">get</a>(...) -> ApiResponseTemplateOut</code></summary>
<dl>
<dd>

#### 📝 Description

<dl>
<dd>

<dl>
<dd>

Fetch a template by id if visible (own, public, or starter).

Dual-auth: Clerk JWT or `op_live_*` API key (scope `templates:read`).
</dd>
</dl>
</dd>
</dl>

#### 🔌 Usage

<dl>
<dd>

<dl>
<dd>

```python
from onepin import OnePinClient
from onepin.environment import OnePinClientEnvironment

client = OnePinClient(
    token="<token>",
    environment=OnePinClientEnvironment.PROD,
)

client.templates.get(
    template_id="template_id",
)

```
</dd>
</dl>
</dd>
</dl>

#### ⚙️ Parameters

<dl>
<dd>

<dl>
<dd>

**template_id:** `str` 
    
</dd>
</dl>

<dl>
<dd>

**workspace_id:** `typing.Optional[str]` 
    
</dd>
</dl>

<dl>
<dd>

**request_options:** `typing.Optional[RequestOptions]` — Request-specific configuration.
    
</dd>
</dl>
</dd>
</dl>


</dd>
</dl>
</details>

<details><summary><code>client.templates.<a href="src/onepin/templates/client.py">delete_template</a>(...) -> ApiResponseDict</code></summary>
<dl>
<dd>

#### 📝 Description

<dl>
<dd>

<dl>
<dd>

Soft-delete a template. Owner only; starter templates are read-only.
</dd>
</dl>
</dd>
</dl>

#### 🔌 Usage

<dl>
<dd>

<dl>
<dd>

```python
from onepin import OnePinClient
from onepin.environment import OnePinClientEnvironment

client = OnePinClient(
    token="<token>",
    environment=OnePinClientEnvironment.PROD,
)

client.templates.delete_template(
    template_id="template_id",
)

```
</dd>
</dl>
</dd>
</dl>

#### ⚙️ Parameters

<dl>
<dd>

<dl>
<dd>

**template_id:** `str` 
    
</dd>
</dl>

<dl>
<dd>

**workspace_id:** `typing.Optional[str]` 
    
</dd>
</dl>

<dl>
<dd>

**request_options:** `typing.Optional[RequestOptions]` — Request-specific configuration.
    
</dd>
</dl>
</dd>
</dl>


</dd>
</dl>
</details>

<details><summary><code>client.templates.<a href="src/onepin/templates/client.py">update_template</a>(...) -> ApiResponseTemplateOut</code></summary>
<dl>
<dd>

#### 📝 Description

<dl>
<dd>

<dl>
<dd>

Update a template. Owner only; starter templates are read-only.

`definition` is full-replace (matches `WorkflowUpdate` — the FE sends the
entire graph back on save). Other fields are partial via `exclude_unset`.
</dd>
</dl>
</dd>
</dl>

#### 🔌 Usage

<dl>
<dd>

<dl>
<dd>

```python
from onepin import OnePinClient
from onepin.environment import OnePinClientEnvironment

client = OnePinClient(
    token="<token>",
    environment=OnePinClientEnvironment.PROD,
)

client.templates.update_template(
    template_id="template_id",
)

```
</dd>
</dl>
</dd>
</dl>

#### ⚙️ Parameters

<dl>
<dd>

<dl>
<dd>

**template_id:** `str` 
    
</dd>
</dl>

<dl>
<dd>

**workspace_id:** `typing.Optional[str]` 
    
</dd>
</dl>

<dl>
<dd>

**name:** `typing.Optional[str]` 
    
</dd>
</dl>

<dl>
<dd>

**description:** `typing.Optional[str]` 
    
</dd>
</dl>

<dl>
<dd>

**category:** `typing.Optional[TemplateCategory]` 
    
</dd>
</dl>

<dl>
<dd>

**definition:** `typing.Optional[WorkflowDefinitionInput]` — Full-replace on PATCH. Omit to keep the stored value. Explicit `null` is rejected — there is no 'empty graph' use-case worth the ambiguity. The union with `null` here only makes omission easy for FE clients; see `reject_null_definition` for the runtime guard.
    
</dd>
</dl>

<dl>
<dd>

**request_options:** `typing.Optional[RequestOptions]` — Request-specific configuration.
    
</dd>
</dl>
</dd>
</dl>


</dd>
</dl>
</details>

<details><summary><code>client.templates.<a href="src/onepin/templates/client.py">estimate_template</a>(...) -> ApiResponseTemplateEstimateResponse</code></summary>
<dl>
<dd>

#### 📝 Description

<dl>
<dd>

<dl>
<dd>

Return per-1,000-character pricing for a visible template snapshot.
</dd>
</dl>
</dd>
</dl>

#### 🔌 Usage

<dl>
<dd>

<dl>
<dd>

```python
from onepin import OnePinClient
from onepin.environment import OnePinClientEnvironment

client = OnePinClient(
    token="<token>",
    environment=OnePinClientEnvironment.PROD,
)

client.templates.estimate_template(
    template_id="template_id",
)

```
</dd>
</dl>
</dd>
</dl>

#### ⚙️ Parameters

<dl>
<dd>

<dl>
<dd>

**template_id:** `str` 
    
</dd>
</dl>

<dl>
<dd>

**workspace_id:** `typing.Optional[str]` 
    
</dd>
</dl>

<dl>
<dd>

**request_options:** `typing.Optional[RequestOptions]` — Request-specific configuration.
    
</dd>
</dl>
</dd>
</dl>


</dd>
</dl>
</details>

<details><summary><code>client.templates.<a href="src/onepin/templates/client.py">clone</a>(...) -> ApiResponseWorkflowOut</code></summary>
<dl>
<dd>

#### 📝 Description

<dl>
<dd>

<dl>
<dd>

Clone a template into a workflow in the caller's workspace.

Dual-auth: Clerk JWT or `op_live_*` API key (scope `workflows:write`).

Same-workspace clones use the live `definition` (owner authoring).
Cross-workspace clones use the `published_definition` snapshot to avoid
leaking unpublished draft edits.

Resolved name: explicit `body.name` (stripped) OR fallback to
`"{source_name} (Copy)"`.
</dd>
</dl>
</dd>
</dl>

#### 🔌 Usage

<dl>
<dd>

<dl>
<dd>

```python
from onepin import OnePinClient
from onepin.environment import OnePinClientEnvironment

client = OnePinClient(
    token="<token>",
    environment=OnePinClientEnvironment.PROD,
)

client.templates.clone(
    template_id="template_id",
)

```
</dd>
</dl>
</dd>
</dl>

#### ⚙️ Parameters

<dl>
<dd>

<dl>
<dd>

**template_id:** `str` 
    
</dd>
</dl>

<dl>
<dd>

**workspace_id:** `typing.Optional[str]` 
    
</dd>
</dl>

<dl>
<dd>

**name:** `typing.Optional[str]` 
    
</dd>
</dl>

<dl>
<dd>

**request_options:** `typing.Optional[RequestOptions]` — Request-specific configuration.
    
</dd>
</dl>
</dd>
</dl>


</dd>
</dl>
</details>

<details><summary><code>client.templates.<a href="src/onepin/templates/client.py">favorite_template</a>(...) -> ApiResponseTemplateOut</code></summary>
<dl>
<dd>

#### 📝 Description

<dl>
<dd>

<dl>
<dd>

Mark a visible template as a favorite for the current user.

Authenticated but not workspace-scoped — favorites are cross-workspace by
design for public/starter templates and for the caller's own private
templates when they still belong to that template's workspace.

Returns 404 when the template does not exist or is not visible to the
caller. This POST intentionally enumerates success/failure for the toggle
UX, while DELETE stays non-enumerating.
</dd>
</dl>
</dd>
</dl>

#### 🔌 Usage

<dl>
<dd>

<dl>
<dd>

```python
from onepin import OnePinClient
from onepin.environment import OnePinClientEnvironment

client = OnePinClient(
    token="<token>",
    environment=OnePinClientEnvironment.PROD,
)

client.templates.favorite_template(
    template_id="template_id",
)

```
</dd>
</dl>
</dd>
</dl>

#### ⚙️ Parameters

<dl>
<dd>

<dl>
<dd>

**template_id:** `str` 
    
</dd>
</dl>

<dl>
<dd>

**request_options:** `typing.Optional[RequestOptions]` — Request-specific configuration.
    
</dd>
</dl>
</dd>
</dl>


</dd>
</dl>
</details>

<details><summary><code>client.templates.<a href="src/onepin/templates/client.py">unfavorite_template</a>(...) -> ApiResponseDict</code></summary>
<dl>
<dd>

#### 📝 Description

<dl>
<dd>

<dl>
<dd>

Remove a template favorite for the current user.

Deletion is intentionally non-enumerating: authenticated callers receive a
successful empty response whether the row or template exists.
</dd>
</dl>
</dd>
</dl>

#### 🔌 Usage

<dl>
<dd>

<dl>
<dd>

```python
from onepin import OnePinClient
from onepin.environment import OnePinClientEnvironment

client = OnePinClient(
    token="<token>",
    environment=OnePinClientEnvironment.PROD,
)

client.templates.unfavorite_template(
    template_id="template_id",
)

```
</dd>
</dl>
</dd>
</dl>

#### ⚙️ Parameters

<dl>
<dd>

<dl>
<dd>

**template_id:** `str` 
    
</dd>
</dl>

<dl>
<dd>

**request_options:** `typing.Optional[RequestOptions]` — Request-specific configuration.
    
</dd>
</dl>
</dd>
</dl>


</dd>
</dl>
</details>

## voices
<details><summary><code>client.voices.<a href="src/onepin/voices/client.py">list</a>(...) -> ApiCountedListResponseVoiceOut</code></summary>
<dl>
<dd>

#### 📝 Description

<dl>
<dd>

<dl>
<dd>

List TTS voices available to the current workspace.

Every filter accepts repeat-key OR semantics:
`?gender=female&gender=neutral&category=narration&source=platform&source=workspace`.
Filters combine across fields with AND; within a field, values OR.

`language` uses Postgres `?|` (exists-any) against `voices.supported_languages`.
Platform voices with NULL `supported_languages` (catalog gaps) are treated
as general-use and match every locale filter. User-uploaded / cloned voices
with NULL stay excluded — NULL there means "language unknown" pending the
clone flow's language detection.

Multi-sort: `sort` and `order` are parallel lists. `?sort=uses_count&sort=name&order=desc&order=asc`
orders primarily by uses_count DESC, secondarily by name ASC. When `order`
is shorter than `sort`, missing entries default per-field:
`name=asc, created_at=desc, uses_count=desc`. When `sort` is omitted, list
defaults to newest-first (or most-recently-favorited-first if
`favorites_only=true`). Every sort path appends `Voice.id ASC` as a
deterministic tiebreaker for pagination stability.
</dd>
</dl>
</dd>
</dl>

#### 🔌 Usage

<dl>
<dd>

<dl>
<dd>

```python
from onepin import OnePinClient
from onepin.environment import OnePinClientEnvironment

client = OnePinClient(
    token="<token>",
    environment=OnePinClientEnvironment.PROD,
)

client.voices.list()

```
</dd>
</dl>
</dd>
</dl>

#### ⚙️ Parameters

<dl>
<dd>

<dl>
<dd>

**offset:** `typing.Optional[int]` 
    
</dd>
</dl>

<dl>
<dd>

**limit:** `typing.Optional[int]` 
    
</dd>
</dl>

<dl>
<dd>

**favorites_only:** `typing.Optional[bool]` 
    
</dd>
</dl>

<dl>
<dd>

**source:** `typing.Optional[typing.List[ListVoicesRequestSourceItem]]` — Repeat for OR across scopes
    
</dd>
</dl>

<dl>
<dd>

**gender:** `typing.Optional[typing.List[VoiceGender]]` — Repeat for OR
    
</dd>
</dl>

<dl>
<dd>

**age:** `typing.Optional[typing.List[VoiceAge]]` — Repeat for OR
    
</dd>
</dl>

<dl>
<dd>

**category:** `typing.Optional[typing.List[VoiceCategory]]` — Repeat for OR
    
</dd>
</dl>

<dl>
<dd>

**accent:** `typing.Optional[typing.List[VoiceAccent]]` — Repeat for OR
    
</dd>
</dl>

<dl>
<dd>

**search:** `typing.Optional[str]` 
    
</dd>
</dl>

<dl>
<dd>

**sort:** `typing.Optional[typing.List[ListVoicesRequestSortItem]]` — Repeat for multi-sort. Pairs with `order` index-wise.
    
</dd>
</dl>

<dl>
<dd>

**order:** `typing.Optional[typing.List[ListVoicesRequestOrderItem]]` — Parallel to sort[]; shorter is padded with per-field defaults.
    
</dd>
</dl>

<dl>
<dd>

**provider:** `typing.Optional[typing.List[ListVoicesRequestProviderItem]]` — Repeat for OR, e.g. ?provider=elevenlabs&provider=rime
    
</dd>
</dl>

<dl>
<dd>

**model:** `typing.Optional[typing.List[str]]` — Repeat for OR. Filters platform voices by TTS model, e.g. ?model=arcana&model=sonic-2
    
</dd>
</dl>

<dl>
<dd>

**language:** `typing.Optional[typing.List[ListVoicesRequestLanguageItem]]` — Repeat for OR, e.g. ?language=en-us&language=ko-kr
    
</dd>
</dl>

<dl>
<dd>

**workspace_id:** `typing.Optional[str]` 
    
</dd>
</dl>

<dl>
<dd>

**request_options:** `typing.Optional[RequestOptions]` — Request-specific configuration.
    
</dd>
</dl>
</dd>
</dl>


</dd>
</dl>
</details>

<details><summary><code>client.voices.<a href="src/onepin/voices/client.py">get</a>(...) -> ApiResponseVoiceOut</code></summary>
<dl>
<dd>

#### 📝 Description

<dl>
<dd>

<dl>
<dd>

Get a voice by ID, scoped to caller workspace + platform voices.
</dd>
</dl>
</dd>
</dl>

#### 🔌 Usage

<dl>
<dd>

<dl>
<dd>

```python
from onepin import OnePinClient
from onepin.environment import OnePinClientEnvironment

client = OnePinClient(
    token="<token>",
    environment=OnePinClientEnvironment.PROD,
)

client.voices.get(
    voice_id="voice_id",
)

```
</dd>
</dl>
</dd>
</dl>

#### ⚙️ Parameters

<dl>
<dd>

<dl>
<dd>

**voice_id:** `str` 
    
</dd>
</dl>

<dl>
<dd>

**workspace_id:** `typing.Optional[str]` 
    
</dd>
</dl>

<dl>
<dd>

**request_options:** `typing.Optional[RequestOptions]` — Request-specific configuration.
    
</dd>
</dl>
</dd>
</dl>


</dd>
</dl>
</details>

<details><summary><code>client.voices.<a href="src/onepin/voices/client.py">similar</a>(...) -> ApiListResponseVoiceSimilarOut</code></summary>
<dl>
<dd>

#### 📝 Description

<dl>
<dd>

<dl>
<dd>

Return voices nearest to a reference voice embedding.
</dd>
</dl>
</dd>
</dl>

#### 🔌 Usage

<dl>
<dd>

<dl>
<dd>

```python
from onepin import OnePinClient
from onepin.environment import OnePinClientEnvironment

client = OnePinClient(
    token="<token>",
    environment=OnePinClientEnvironment.PROD,
)

client.voices.similar(
    voice_id="voice_id",
)

```
</dd>
</dl>
</dd>
</dl>

#### ⚙️ Parameters

<dl>
<dd>

<dl>
<dd>

**voice_id:** `str` 
    
</dd>
</dl>

<dl>
<dd>

**limit:** `typing.Optional[int]` 
    
</dd>
</dl>

<dl>
<dd>

**language:** `typing.Optional[typing.List[str]]` — Repeat for OR, e.g. ?language=en-us&language=ko-kr
    
</dd>
</dl>

<dl>
<dd>

**workspace_id:** `typing.Optional[str]` 
    
</dd>
</dl>

<dl>
<dd>

**request_options:** `typing.Optional[RequestOptions]` — Request-specific configuration.
    
</dd>
</dl>
</dd>
</dl>


</dd>
</dl>
</details>

<details><summary><code>client.voices.<a href="src/onepin/voices/client.py">favorite_voice</a>(...) -> ApiResponseVoiceOut</code></summary>
<dl>
<dd>

#### 📝 Description

<dl>
<dd>

<dl>
<dd>

Mark a voice as a workspace favorite.
</dd>
</dl>
</dd>
</dl>

#### 🔌 Usage

<dl>
<dd>

<dl>
<dd>

```python
from onepin import OnePinClient
from onepin.environment import OnePinClientEnvironment

client = OnePinClient(
    token="<token>",
    environment=OnePinClientEnvironment.PROD,
)

client.voices.favorite_voice(
    voice_id="voice_id",
)

```
</dd>
</dl>
</dd>
</dl>

#### ⚙️ Parameters

<dl>
<dd>

<dl>
<dd>

**voice_id:** `str` 
    
</dd>
</dl>

<dl>
<dd>

**workspace_id:** `typing.Optional[str]` 
    
</dd>
</dl>

<dl>
<dd>

**request_options:** `typing.Optional[RequestOptions]` — Request-specific configuration.
    
</dd>
</dl>
</dd>
</dl>


</dd>
</dl>
</details>

<details><summary><code>client.voices.<a href="src/onepin/voices/client.py">unfavorite_voice</a>(...) -> ApiResponseDict</code></summary>
<dl>
<dd>

#### 📝 Description

<dl>
<dd>

<dl>
<dd>

Remove a voice from workspace favorites.
</dd>
</dl>
</dd>
</dl>

#### 🔌 Usage

<dl>
<dd>

<dl>
<dd>

```python
from onepin import OnePinClient
from onepin.environment import OnePinClientEnvironment

client = OnePinClient(
    token="<token>",
    environment=OnePinClientEnvironment.PROD,
)

client.voices.unfavorite_voice(
    voice_id="voice_id",
)

```
</dd>
</dl>
</dd>
</dl>

#### ⚙️ Parameters

<dl>
<dd>

<dl>
<dd>

**voice_id:** `str` 
    
</dd>
</dl>

<dl>
<dd>

**workspace_id:** `typing.Optional[str]` 
    
</dd>
</dl>

<dl>
<dd>

**request_options:** `typing.Optional[RequestOptions]` — Request-specific configuration.
    
</dd>
</dl>
</dd>
</dl>


</dd>
</dl>
</details>

## workspace
<details><summary><code>client.workspace.<a href="src/onepin/workspace/client.py">get_workspace_settings</a>(...) -> ApiResponseWorkspaceSettingsOut</code></summary>
<dl>
<dd>

#### 📝 Description

<dl>
<dd>

<dl>
<dd>

Return workspace-level settings (default_language, theme).

Settings are workspace-scoped: every member of the workspace sees the
same defaults. Per-user UI preferences (e.g. personal dark-mode) belong
in a future user_settings endpoint.

Path-based authorization (via get_workspace_from_path_for_auth_context) prevents the
header-vs-path bypass class — the {ws_id} URL segment is the source of
truth for which workspace is being read.
</dd>
</dl>
</dd>
</dl>

#### 🔌 Usage

<dl>
<dd>

<dl>
<dd>

```python
from onepin import OnePinClient
from onepin.environment import OnePinClientEnvironment

client = OnePinClient(
    token="<token>",
    environment=OnePinClientEnvironment.PROD,
)

client.workspace.get_workspace_settings(
    ws_id="ws_id",
)

```
</dd>
</dl>
</dd>
</dl>

#### ⚙️ Parameters

<dl>
<dd>

<dl>
<dd>

**ws_id:** `str` 
    
</dd>
</dl>

<dl>
<dd>

**request_options:** `typing.Optional[RequestOptions]` — Request-specific configuration.
    
</dd>
</dl>
</dd>
</dl>


</dd>
</dl>
</details>

## workspace-aggregates
<details><summary><code>client.workspace_aggregates.<a href="src/onepin/workspace_aggregates/client.py">workspace_runs_stats</a>(...) -> ApiResponseWorkspaceRunsStatsOut</code></summary>
<dl>
<dd>

#### 📝 Description

<dl>
<dd>

<dl>
<dd>

Aggregate workflow-run counts grouped by raw RunStatus across the workspace.
</dd>
</dl>
</dd>
</dl>

#### 🔌 Usage

<dl>
<dd>

<dl>
<dd>

```python
from onepin import OnePinClient
from onepin.environment import OnePinClientEnvironment

client = OnePinClient(
    token="<token>",
    environment=OnePinClientEnvironment.PROD,
)

client.workspace_aggregates.workspace_runs_stats()

```
</dd>
</dl>
</dd>
</dl>

#### ⚙️ Parameters

<dl>
<dd>

<dl>
<dd>

**from:** `typing.Optional[datetime.datetime]` — Filter runs by created_at >= this ISO datetime.
    
</dd>
</dl>

<dl>
<dd>

**to:** `typing.Optional[datetime.datetime]` — Filter runs by created_at <= this ISO datetime.
    
</dd>
</dl>

<dl>
<dd>

**workspace_id:** `typing.Optional[str]` 
    
</dd>
</dl>

<dl>
<dd>

**request_options:** `typing.Optional[RequestOptions]` — Request-specific configuration.
    
</dd>
</dl>
</dd>
</dl>


</dd>
</dl>
</details>

<details><summary><code>client.workspace_aggregates.<a href="src/onepin/workspace_aggregates/client.py">workspace_workflows_stats</a>(...) -> ApiResponseWorkspaceWorkflowsStatsOut</code></summary>
<dl>
<dd>

#### 📝 Description

<dl>
<dd>

<dl>
<dd>

Aggregate workflow counts grouped by derived WorkflowListStatus across the workspace.
</dd>
</dl>
</dd>
</dl>

#### 🔌 Usage

<dl>
<dd>

<dl>
<dd>

```python
from onepin import OnePinClient
from onepin.environment import OnePinClientEnvironment

client = OnePinClient(
    token="<token>",
    environment=OnePinClientEnvironment.PROD,
)

client.workspace_aggregates.workspace_workflows_stats()

```
</dd>
</dl>
</dd>
</dl>

#### ⚙️ Parameters

<dl>
<dd>

<dl>
<dd>

**from:** `typing.Optional[datetime.datetime]` — Filter workflows by created_at >= this ISO datetime.
    
</dd>
</dl>

<dl>
<dd>

**to:** `typing.Optional[datetime.datetime]` — Filter workflows by created_at <= this ISO datetime.
    
</dd>
</dl>

<dl>
<dd>

**workspace_id:** `typing.Optional[str]` 
    
</dd>
</dl>

<dl>
<dd>

**request_options:** `typing.Optional[RequestOptions]` — Request-specific configuration.
    
</dd>
</dl>
</dd>
</dl>


</dd>
</dl>
</details>

## workspace-members
<details><summary><code>client.workspace_members.<a href="src/onepin/workspace_members/client.py">list_members</a>(...) -> ApiListResponseWorkspaceMemberOut</code></summary>
<dl>
<dd>

#### 📝 Description

<dl>
<dd>

<dl>
<dd>

List active members and pending invites for a workspace.
</dd>
</dl>
</dd>
</dl>

#### 🔌 Usage

<dl>
<dd>

<dl>
<dd>

```python
from onepin import OnePinClient
from onepin.environment import OnePinClientEnvironment

client = OnePinClient(
    token="<token>",
    environment=OnePinClientEnvironment.PROD,
)

client.workspace_members.list_members(
    ws_id="ws_id",
)

```
</dd>
</dl>
</dd>
</dl>

#### ⚙️ Parameters

<dl>
<dd>

<dl>
<dd>

**ws_id:** `str` 
    
</dd>
</dl>

<dl>
<dd>

**request_options:** `typing.Optional[RequestOptions]` — Request-specific configuration.
    
</dd>
</dl>
</dd>
</dl>


</dd>
</dl>
</details>

<details><summary><code>client.workspace_members.<a href="src/onepin/workspace_members/client.py">create_invite</a>(...) -> ApiResponseWorkspaceInviteOut</code></summary>
<dl>
<dd>

#### 📝 Description

<dl>
<dd>

<dl>
<dd>

Invite a user to the workspace via email.

POD-301: gated by `seats` plan limit on the workspace owner's plan.
Active members + pending invites both count against the cap.
</dd>
</dl>
</dd>
</dl>

#### 🔌 Usage

<dl>
<dd>

<dl>
<dd>

```python
from onepin import OnePinClient
from onepin.environment import OnePinClientEnvironment

client = OnePinClient(
    token="<token>",
    environment=OnePinClientEnvironment.PROD,
)

client.workspace_members.create_invite(
    ws_id="ws_id",
    email="email",
    role="admin",
)

```
</dd>
</dl>
</dd>
</dl>

#### ⚙️ Parameters

<dl>
<dd>

<dl>
<dd>

**ws_id:** `str` 
    
</dd>
</dl>

<dl>
<dd>

**email:** `str` 
    
</dd>
</dl>

<dl>
<dd>

**role:** `WorkspaceRole` 
    
</dd>
</dl>

<dl>
<dd>

**request_options:** `typing.Optional[RequestOptions]` — Request-specific configuration.
    
</dd>
</dl>
</dd>
</dl>


</dd>
</dl>
</details>

<details><summary><code>client.workspace_members.<a href="src/onepin/workspace_members/client.py">remove_member</a>(...) -> ApiResponseDict</code></summary>
<dl>
<dd>

#### 📝 Description

<dl>
<dd>

<dl>
<dd>

Remove an active member. Admin only.
</dd>
</dl>
</dd>
</dl>

#### 🔌 Usage

<dl>
<dd>

<dl>
<dd>

```python
from onepin import OnePinClient
from onepin.environment import OnePinClientEnvironment

client = OnePinClient(
    token="<token>",
    environment=OnePinClientEnvironment.PROD,
)

client.workspace_members.remove_member(
    ws_id="ws_id",
    member_id="member_id",
)

```
</dd>
</dl>
</dd>
</dl>

#### ⚙️ Parameters

<dl>
<dd>

<dl>
<dd>

**ws_id:** `str` 
    
</dd>
</dl>

<dl>
<dd>

**member_id:** `str` 
    
</dd>
</dl>

<dl>
<dd>

**request_options:** `typing.Optional[RequestOptions]` — Request-specific configuration.
    
</dd>
</dl>
</dd>
</dl>


</dd>
</dl>
</details>

<details><summary><code>client.workspace_members.<a href="src/onepin/workspace_members/client.py">update_member_role</a>(...) -> ApiResponseDict</code></summary>
<dl>
<dd>

#### 📝 Description

<dl>
<dd>

<dl>
<dd>

Change a member's role. Admin only.
</dd>
</dl>
</dd>
</dl>

#### 🔌 Usage

<dl>
<dd>

<dl>
<dd>

```python
from onepin import OnePinClient
from onepin.environment import OnePinClientEnvironment

client = OnePinClient(
    token="<token>",
    environment=OnePinClientEnvironment.PROD,
)

client.workspace_members.update_member_role(
    ws_id="ws_id",
    member_id="member_id",
    role="admin",
)

```
</dd>
</dl>
</dd>
</dl>

#### ⚙️ Parameters

<dl>
<dd>

<dl>
<dd>

**ws_id:** `str` 
    
</dd>
</dl>

<dl>
<dd>

**member_id:** `str` 
    
</dd>
</dl>

<dl>
<dd>

**request:** `WorkspaceMemberRoleUpdate` 
    
</dd>
</dl>

<dl>
<dd>

**request_options:** `typing.Optional[RequestOptions]` — Request-specific configuration.
    
</dd>
</dl>
</dd>
</dl>


</dd>
</dl>
</details>

<details><summary><code>client.workspace_members.<a href="src/onepin/workspace_members/client.py">revoke_invite</a>(...) -> ApiResponseDict</code></summary>
<dl>
<dd>

#### 📝 Description

<dl>
<dd>

<dl>
<dd>

Revoke a pending invite. Admin only.
</dd>
</dl>
</dd>
</dl>

#### 🔌 Usage

<dl>
<dd>

<dl>
<dd>

```python
from onepin import OnePinClient
from onepin.environment import OnePinClientEnvironment

client = OnePinClient(
    token="<token>",
    environment=OnePinClientEnvironment.PROD,
)

client.workspace_members.revoke_invite(
    ws_id="ws_id",
    invite_id="invite_id",
)

```
</dd>
</dl>
</dd>
</dl>

#### ⚙️ Parameters

<dl>
<dd>

<dl>
<dd>

**ws_id:** `str` 
    
</dd>
</dl>

<dl>
<dd>

**invite_id:** `str` 
    
</dd>
</dl>

<dl>
<dd>

**request_options:** `typing.Optional[RequestOptions]` — Request-specific configuration.
    
</dd>
</dl>
</dd>
</dl>


</dd>
</dl>
</details>

<details><summary><code>client.workspace_members.<a href="src/onepin/workspace_members/client.py">update_invite_role</a>(...) -> ApiResponseWorkspaceInviteOut</code></summary>
<dl>
<dd>

#### 📝 Description

<dl>
<dd>

<dl>
<dd>

Update role on a pending invite. Admin only.
</dd>
</dl>
</dd>
</dl>

#### 🔌 Usage

<dl>
<dd>

<dl>
<dd>

```python
from onepin import OnePinClient
from onepin.environment import OnePinClientEnvironment

client = OnePinClient(
    token="<token>",
    environment=OnePinClientEnvironment.PROD,
)

client.workspace_members.update_invite_role(
    ws_id="ws_id",
    invite_id="invite_id",
    role="admin",
)

```
</dd>
</dl>
</dd>
</dl>

#### ⚙️ Parameters

<dl>
<dd>

<dl>
<dd>

**ws_id:** `str` 
    
</dd>
</dl>

<dl>
<dd>

**invite_id:** `str` 
    
</dd>
</dl>

<dl>
<dd>

**request:** `WorkspaceMemberRoleUpdate` 
    
</dd>
</dl>

<dl>
<dd>

**request_options:** `typing.Optional[RequestOptions]` — Request-specific configuration.
    
</dd>
</dl>
</dd>
</dl>


</dd>
</dl>
</details>

<details><summary><code>client.workspace_members.<a href="src/onepin/workspace_members/client.py">accept_invite</a>(...) -> ApiResponseDict</code></summary>
<dl>
<dd>

#### 📝 Description

<dl>
<dd>

<dl>
<dd>

Accept a workspace invite. Authenticated; validates email match.

POD-301: re-checks `seats` against owner's plan at accept time — owner may
have downgraded since invite sent.
</dd>
</dl>
</dd>
</dl>

#### 🔌 Usage

<dl>
<dd>

<dl>
<dd>

```python
from onepin import OnePinClient
from onepin.environment import OnePinClientEnvironment

client = OnePinClient(
    token="<token>",
    environment=OnePinClientEnvironment.PROD,
)

client.workspace_members.accept_invite(
    token="token",
)

```
</dd>
</dl>
</dd>
</dl>

#### ⚙️ Parameters

<dl>
<dd>

<dl>
<dd>

**token:** `str` 
    
</dd>
</dl>

<dl>
<dd>

**request_options:** `typing.Optional[RequestOptions]` — Request-specific configuration.
    
</dd>
</dl>
</dd>
</dl>


</dd>
</dl>
</details>

## workspaces
<details><summary><code>client.workspaces.<a href="src/onepin/workspaces/client.py">list_workspaces</a>(...) -> ApiListResponseWorkspaceOut</code></summary>
<dl>
<dd>

#### 📝 Description

<dl>
<dd>

<dl>
<dd>

List workspaces the current user is a member of.
</dd>
</dl>
</dd>
</dl>

#### 🔌 Usage

<dl>
<dd>

<dl>
<dd>

```python
from onepin import OnePinClient
from onepin.environment import OnePinClientEnvironment

client = OnePinClient(
    token="<token>",
    environment=OnePinClientEnvironment.PROD,
)

client.workspaces.list_workspaces()

```
</dd>
</dl>
</dd>
</dl>

#### ⚙️ Parameters

<dl>
<dd>

<dl>
<dd>

**offset:** `typing.Optional[int]` 
    
</dd>
</dl>

<dl>
<dd>

**limit:** `typing.Optional[int]` 
    
</dd>
</dl>

<dl>
<dd>

**request_options:** `typing.Optional[RequestOptions]` — Request-specific configuration.
    
</dd>
</dl>
</dd>
</dl>


</dd>
</dl>
</details>

<details><summary><code>client.workspaces.<a href="src/onepin/workspaces/client.py">create_workspace</a>(...) -> ApiResponseWorkspaceOut</code></summary>
<dl>
<dd>

#### 📝 Description

<dl>
<dd>

<dl>
<dd>

Create a new workspace owned by the current user.

POD-301: gated by `workspaces_per_owner` plan limit. Free=1, Creator=1,
Studio=2, Enterprise=bespoke. Owner soft-deletes don't free up quota until
purge — keeps the gate honest against rapid create/delete cycles.
</dd>
</dl>
</dd>
</dl>

#### 🔌 Usage

<dl>
<dd>

<dl>
<dd>

```python
from onepin import OnePinClient
from onepin.environment import OnePinClientEnvironment

client = OnePinClient(
    token="<token>",
    environment=OnePinClientEnvironment.PROD,
)

client.workspaces.create_workspace(
    name="name",
)

```
</dd>
</dl>
</dd>
</dl>

#### ⚙️ Parameters

<dl>
<dd>

<dl>
<dd>

**name:** `str` 
    
</dd>
</dl>

<dl>
<dd>

**slug:** `typing.Optional[str]` 
    
</dd>
</dl>

<dl>
<dd>

**color_idx:** `typing.Optional[int]` 
    
</dd>
</dl>

<dl>
<dd>

**request_options:** `typing.Optional[RequestOptions]` — Request-specific configuration.
    
</dd>
</dl>
</dd>
</dl>


</dd>
</dl>
</details>

<details><summary><code>client.workspaces.<a href="src/onepin/workspaces/client.py">get_workspace</a>(...) -> ApiResponseWorkspaceOut</code></summary>
<dl>
<dd>

#### 📝 Description

<dl>
<dd>

<dl>
<dd>

Get a workspace the current user is a member of.
</dd>
</dl>
</dd>
</dl>

#### 🔌 Usage

<dl>
<dd>

<dl>
<dd>

```python
from onepin import OnePinClient
from onepin.environment import OnePinClientEnvironment

client = OnePinClient(
    token="<token>",
    environment=OnePinClientEnvironment.PROD,
)

client.workspaces.get_workspace(
    workspace_id="workspace_id",
)

```
</dd>
</dl>
</dd>
</dl>

#### ⚙️ Parameters

<dl>
<dd>

<dl>
<dd>

**workspace_id:** `str` 
    
</dd>
</dl>

<dl>
<dd>

**request_options:** `typing.Optional[RequestOptions]` — Request-specific configuration.
    
</dd>
</dl>
</dd>
</dl>


</dd>
</dl>
</details>

<details><summary><code>client.workspaces.<a href="src/onepin/workspaces/client.py">delete_workspace</a>(...) -> ApiResponseDict</code></summary>
<dl>
<dd>

#### 📝 Description

<dl>
<dd>

<dl>
<dd>

Soft-delete a workspace and cascade soft-delete to its resources.
</dd>
</dl>
</dd>
</dl>

#### 🔌 Usage

<dl>
<dd>

<dl>
<dd>

```python
from onepin import OnePinClient
from onepin.environment import OnePinClientEnvironment

client = OnePinClient(
    token="<token>",
    environment=OnePinClientEnvironment.PROD,
)

client.workspaces.delete_workspace(
    workspace_id="workspace_id",
)

```
</dd>
</dl>
</dd>
</dl>

#### ⚙️ Parameters

<dl>
<dd>

<dl>
<dd>

**workspace_id:** `str` 
    
</dd>
</dl>

<dl>
<dd>

**request_options:** `typing.Optional[RequestOptions]` — Request-specific configuration.
    
</dd>
</dl>
</dd>
</dl>


</dd>
</dl>
</details>

<details><summary><code>client.workspaces.<a href="src/onepin/workspaces/client.py">update_workspace</a>(...) -> ApiResponseWorkspaceOut</code></summary>
<dl>
<dd>

#### 📝 Description

<dl>
<dd>

<dl>
<dd>

Update workspace name, color, and/or slug. Admin only.
</dd>
</dl>
</dd>
</dl>

#### 🔌 Usage

<dl>
<dd>

<dl>
<dd>

```python
from onepin import OnePinClient
from onepin.environment import OnePinClientEnvironment

client = OnePinClient(
    token="<token>",
    environment=OnePinClientEnvironment.PROD,
)

client.workspaces.update_workspace(
    workspace_id="workspace_id",
)

```
</dd>
</dl>
</dd>
</dl>

#### ⚙️ Parameters

<dl>
<dd>

<dl>
<dd>

**workspace_id:** `str` 
    
</dd>
</dl>

<dl>
<dd>

**name:** `typing.Optional[str]` 
    
</dd>
</dl>

<dl>
<dd>

**slug:** `typing.Optional[str]` 
    
</dd>
</dl>

<dl>
<dd>

**color_idx:** `typing.Optional[int]` 
    
</dd>
</dl>

<dl>
<dd>

**request_options:** `typing.Optional[RequestOptions]` — Request-specific configuration.
    
</dd>
</dl>
</dd>
</dl>


</dd>
</dl>
</details>

## uploads
<details><summary><code>client.uploads.<a href="src/onepin/uploads/client.py">create</a>(...) -> ApiResponseUploadCreateResponse</code></summary>
<dl>
<dd>

#### 📝 Description

<dl>
<dd>

<dl>
<dd>

Request a presigned URL for uploading a file.
</dd>
</dl>
</dd>
</dl>

#### 🔌 Usage

<dl>
<dd>

<dl>
<dd>

```python
from onepin import OnePinClient
from onepin.environment import OnePinClientEnvironment

client = OnePinClient(
    token="<token>",
    environment=OnePinClientEnvironment.PROD,
)

client.uploads.create(
    filename="filename",
    category="script",
)

```
</dd>
</dl>
</dd>
</dl>

#### ⚙️ Parameters

<dl>
<dd>

<dl>
<dd>

**filename:** `str` 
    
</dd>
</dl>

<dl>
<dd>

**category:** `UploadRequestCategory` 
    
</dd>
</dl>

<dl>
<dd>

**workspace_id:** `typing.Optional[str]` 
    
</dd>
</dl>

<dl>
<dd>

**request_options:** `typing.Optional[RequestOptions]` — Request-specific configuration.
    
</dd>
</dl>
</dd>
</dl>


</dd>
</dl>
</details>

<details><summary><code>client.uploads.<a href="src/onepin/uploads/client.py">confirm</a>(...) -> ApiResponseUploadOut</code></summary>
<dl>
<dd>

#### 📝 Description

<dl>
<dd>

<dl>
<dd>

Confirm upload and move file to final location.

POD-301: gates the file size against `storage_bytes_per_workspace` whenever
the upload binds to a workspace-scoped resource (header OR derived from
context_id). Records the storage_charge event in the same transaction as the
upload row update.
</dd>
</dl>
</dd>
</dl>

#### 🔌 Usage

<dl>
<dd>

<dl>
<dd>

```python
from onepin import OnePinClient
from onepin.environment import OnePinClientEnvironment

client = OnePinClient(
    token="<token>",
    environment=OnePinClientEnvironment.PROD,
)

client.uploads.confirm(
    upload_id="upload_id",
    context_type="workflow",
    context_id="context_id",
)

```
</dd>
</dl>
</dd>
</dl>

#### ⚙️ Parameters

<dl>
<dd>

<dl>
<dd>

**upload_id:** `str` 
    
</dd>
</dl>

<dl>
<dd>

**context_type:** `UploadConfirmRequestContextType` 
    
</dd>
</dl>

<dl>
<dd>

**context_id:** `str` 
    
</dd>
</dl>

<dl>
<dd>

**workspace_id:** `typing.Optional[str]` 
    
</dd>
</dl>

<dl>
<dd>

**request_options:** `typing.Optional[RequestOptions]` — Request-specific configuration.
    
</dd>
</dl>
</dd>
</dl>


</dd>
</dl>
</details>

<details><summary><code>client.uploads.<a href="src/onepin/uploads/client.py">delete</a>(...) -> ApiResponseDict</code></summary>
<dl>
<dd>

#### 📝 Description

<dl>
<dd>

<dl>
<dd>

Delete an upload and its S3 object.

DB record is deleted first (committed on response). S3 cleanup runs
after the response via a background task so the file is only removed
once the DB commit succeeds.

POD-301: if the upload was confirmed against a workspace-scoped resource,
release the bytes back to that workspace's storage counter. Without this,
storage_bytes_used drifts upward forever and customers stay capped after
deleting files. Read upload state BEFORE delete_for_user — the row is gone
after that call.
</dd>
</dl>
</dd>
</dl>

#### 🔌 Usage

<dl>
<dd>

<dl>
<dd>

```python
from onepin import OnePinClient
from onepin.environment import OnePinClientEnvironment

client = OnePinClient(
    token="<token>",
    environment=OnePinClientEnvironment.PROD,
)

client.uploads.delete(
    upload_id="upload_id",
)

```
</dd>
</dl>
</dd>
</dl>

#### ⚙️ Parameters

<dl>
<dd>

<dl>
<dd>

**upload_id:** `str` 
    
</dd>
</dl>

<dl>
<dd>

**workspace_id:** `typing.Optional[str]` 
    
</dd>
</dl>

<dl>
<dd>

**request_options:** `typing.Optional[RequestOptions]` — Request-specific configuration.
    
</dd>
</dl>
</dd>
</dl>


</dd>
</dl>
</details>

## usage
<details><summary><code>client.usage.<a href="src/onepin/usage/client.py">usage_summary</a>(...) -> ApiResponseUsageSummaryOut</code></summary>
<dl>
<dd>

#### 📝 Description

<dl>
<dd>

<dl>
<dd>

Return workspace usage totals plus tab-specific aggregate activity buckets.
</dd>
</dl>
</dd>
</dl>

#### 🔌 Usage

<dl>
<dd>

<dl>
<dd>

```python
from onepin import OnePinClient
from onepin.environment import OnePinClientEnvironment

client = OnePinClient(
    token="<token>",
    environment=OnePinClientEnvironment.PROD,
)

client.usage.usage_summary()

```
</dd>
</dl>
</dd>
</dl>

#### ⚙️ Parameters

<dl>
<dd>

<dl>
<dd>

**range:** `typing.Optional[UsageSummaryApiV1UsageSummaryGetRequestRange]` — Rolling local calendar-day range.
    
</dd>
</dl>

<dl>
<dd>

**activity_view:** `typing.Optional[UsageSummaryApiV1UsageSummaryGetRequestActivityView]` — Activity chart view: daily=7 local days, weekly=12 Monday-start weeks, monthly=12 months.
    
</dd>
</dl>

<dl>
<dd>

**timezone:** `typing.Optional[str]` — IANA timezone for local day bucketing.
    
</dd>
</dl>

<dl>
<dd>

**workspace_id:** `typing.Optional[str]` 
    
</dd>
</dl>

<dl>
<dd>

**request_options:** `typing.Optional[RequestOptions]` — Request-specific configuration.
    
</dd>
</dl>
</dd>
</dl>


</dd>
</dl>
</details>

<details><summary><code>client.usage.<a href="src/onepin/usage/client.py">usage_by_language</a>(...) -> ApiResponseUsageByLanguageOut</code></summary>
<dl>
<dd>

#### 📝 Description

<dl>
<dd>

<dl>
<dd>

Return workspace generated-audio usage grouped by language.

``share`` is a 0..1 fraction. When ``activity_view`` is supplied, rows use
that tab's local-calendar period; otherwise they preserve legacy ``range``
behavior.
</dd>
</dl>
</dd>
</dl>

#### 🔌 Usage

<dl>
<dd>

<dl>
<dd>

```python
from onepin import OnePinClient
from onepin.environment import OnePinClientEnvironment

client = OnePinClient(
    token="<token>",
    environment=OnePinClientEnvironment.PROD,
)

client.usage.usage_by_language()

```
</dd>
</dl>
</dd>
</dl>

#### ⚙️ Parameters

<dl>
<dd>

<dl>
<dd>

**range:** `typing.Optional[UsageByLanguageApiV1UsageByLanguageGetRequestRange]` — Rolling local calendar-day range.
    
</dd>
</dl>

<dl>
<dd>

**activity_view:** `typing.Optional[UsageByLanguageApiV1UsageByLanguageGetRequestActivityView]` — Optional activity view period to align language rows with the selected Usage tab. When supplied, range is ignored and range in the response is null.
    
</dd>
</dl>

<dl>
<dd>

**timezone:** `typing.Optional[str]` — IANA timezone for local day bucketing.
    
</dd>
</dl>

<dl>
<dd>

**workspace_id:** `typing.Optional[str]` 
    
</dd>
</dl>

<dl>
<dd>

**request_options:** `typing.Optional[RequestOptions]` — Request-specific configuration.
    
</dd>
</dl>
</dd>
</dl>


</dd>
</dl>
</details>

<details><summary><code>client.usage.<a href="src/onepin/usage/client.py">usage_activity</a>(...) -> ApiListResponseUsageActivityOut</code></summary>
<dl>
<dd>

#### 📝 Description

<dl>
<dd>

<dl>
<dd>

Return the workspace usage activity feed with stable action filters and cursor pagination.
</dd>
</dl>
</dd>
</dl>

#### 🔌 Usage

<dl>
<dd>

<dl>
<dd>

```python
from onepin import OnePinClient
from onepin.environment import OnePinClientEnvironment

client = OnePinClient(
    token="<token>",
    environment=OnePinClientEnvironment.PROD,
)

client.usage.usage_activity()

```
</dd>
</dl>
</dd>
</dl>

#### ⚙️ Parameters

<dl>
<dd>

<dl>
<dd>

**range:** `typing.Optional[UsageActivityApiV1UsageActivityGetRequestRange]` — Rolling local calendar-day range.
    
</dd>
</dl>

<dl>
<dd>

**type:** `typing.Optional[UsageActivityAction]` — Filter by usage activity type.
    
</dd>
</dl>

<dl>
<dd>

**user_id:** `typing.Optional[str]` — Filter by actor user id.
    
</dd>
</dl>

<dl>
<dd>

**limit:** `typing.Optional[int]` 
    
</dd>
</dl>

<dl>
<dd>

**cursor:** `typing.Optional[str]` — Opaque pagination cursor.
    
</dd>
</dl>

<dl>
<dd>

**timezone:** `typing.Optional[str]` — IANA timezone for local day bucketing.
    
</dd>
</dl>

<dl>
<dd>

**workspace_id:** `typing.Optional[str]` 
    
</dd>
</dl>

<dl>
<dd>

**request_options:** `typing.Optional[RequestOptions]` — Request-specific configuration.
    
</dd>
</dl>
</dd>
</dl>


</dd>
</dl>
</details>

## billing
<details><summary><code>client.billing.<a href="src/onepin/billing/client.py">list_plans</a>() -> ApiListResponseCustomerPlanResponse</code></summary>
<dl>
<dd>

#### 📝 Description

<dl>
<dd>

<dl>
<dd>

List subscription plans and features (public, no authentication).

Public so the marketing site (Framer) can render live pricing without a
Clerk session. Returns the same active, non-custom plan catalog as before
(name, price, interval, limits, localized ``plan_details``). Honors
``X-Language`` / ``Accept-Language`` for ``plan_details`` (defaults ``en``).
</dd>
</dl>
</dd>
</dl>

#### 🔌 Usage

<dl>
<dd>

<dl>
<dd>

```python
from onepin import OnePinClient
from onepin.environment import OnePinClientEnvironment

client = OnePinClient(
    token="<token>",
    environment=OnePinClientEnvironment.PROD,
)

client.billing.list_plans()

```
</dd>
</dl>
</dd>
</dl>

#### ⚙️ Parameters

<dl>
<dd>

<dl>
<dd>

**request_options:** `typing.Optional[RequestOptions]` — Request-specific configuration.
    
</dd>
</dl>
</dd>
</dl>


</dd>
</dl>
</details>

<details><summary><code>client.billing.<a href="src/onepin/billing/client.py">preview_plan_change</a>(...) -> ApiResponseCustomerPlanChangePreviewResponse</code></summary>
<dl>
<dd>

#### 📝 Description

<dl>
<dd>

<dl>
<dd>

Preview the cost of changing to the given plan.
</dd>
</dl>
</dd>
</dl>

#### 🔌 Usage

<dl>
<dd>

<dl>
<dd>

```python
from onepin import OnePinClient
from onepin.environment import OnePinClientEnvironment

client = OnePinClient(
    token="<token>",
    environment=OnePinClientEnvironment.PROD,
)

client.billing.preview_plan_change(
    plan_id="plan_id",
)

```
</dd>
</dl>
</dd>
</dl>

#### ⚙️ Parameters

<dl>
<dd>

<dl>
<dd>

**plan_id:** `str` 
    
</dd>
</dl>

<dl>
<dd>

**request_options:** `typing.Optional[RequestOptions]` — Request-specific configuration.
    
</dd>
</dl>
</dd>
</dl>


</dd>
</dl>
</details>

<details><summary><code>client.billing.<a href="src/onepin/billing/client.py">create_checkout</a>(...) -> ApiResponseCheckoutResponse</code></summary>
<dl>
<dd>

#### 📝 Description

<dl>
<dd>

<dl>
<dd>

Create a Stripe Checkout session for the given plan.
</dd>
</dl>
</dd>
</dl>

#### 🔌 Usage

<dl>
<dd>

<dl>
<dd>

```python
from onepin import OnePinClient
from onepin.environment import OnePinClientEnvironment

client = OnePinClient(
    token="<token>",
    environment=OnePinClientEnvironment.PROD,
)

client.billing.create_checkout(
    plan_id="plan_id",
    return_url="return_url",
)

```
</dd>
</dl>
</dd>
</dl>

#### ⚙️ Parameters

<dl>
<dd>

<dl>
<dd>

**plan_id:** `str` 
    
</dd>
</dl>

<dl>
<dd>

**return_url:** `str` 
    
</dd>
</dl>

<dl>
<dd>

**request_options:** `typing.Optional[RequestOptions]` — Request-specific configuration.
    
</dd>
</dl>
</dd>
</dl>


</dd>
</dl>
</details>

## users
<details><summary><code>client.users.<a href="src/onepin/users/client.py">get_current_subscription</a>() -> ApiResponseUnionCustomerSubscriptionResponseNoneType</code></summary>
<dl>
<dd>

#### 📝 Description

<dl>
<dd>

<dl>
<dd>

Get the current user's active subscription.
</dd>
</dl>
</dd>
</dl>

#### 🔌 Usage

<dl>
<dd>

<dl>
<dd>

```python
from onepin import OnePinClient
from onepin.environment import OnePinClientEnvironment

client = OnePinClient(
    token="<token>",
    environment=OnePinClientEnvironment.PROD,
)

client.users.get_current_subscription()

```
</dd>
</dl>
</dd>
</dl>

#### ⚙️ Parameters

<dl>
<dd>

<dl>
<dd>

**request_options:** `typing.Optional[RequestOptions]` — Request-specific configuration.
    
</dd>
</dl>
</dd>
</dl>


</dd>
</dl>
</details>

<details><summary><code>client.users.<a href="src/onepin/users/client.py">subscribe</a>(...) -> ApiResponseCustomerSubscriptionResponse</code></summary>
<dl>
<dd>

#### 📝 Description

<dl>
<dd>

<dl>
<dd>

Create a subscription using the default payment method.
</dd>
</dl>
</dd>
</dl>

#### 🔌 Usage

<dl>
<dd>

<dl>
<dd>

```python
from onepin import OnePinClient
from onepin.environment import OnePinClientEnvironment

client = OnePinClient(
    token="<token>",
    environment=OnePinClientEnvironment.PROD,
)

client.users.subscribe(
    plan_id="plan_id",
)

```
</dd>
</dl>
</dd>
</dl>

#### ⚙️ Parameters

<dl>
<dd>

<dl>
<dd>

**plan_id:** `str` 
    
</dd>
</dl>

<dl>
<dd>

**request_options:** `typing.Optional[RequestOptions]` — Request-specific configuration.
    
</dd>
</dl>
</dd>
</dl>


</dd>
</dl>
</details>

<details><summary><code>client.users.<a href="src/onepin/users/client.py">cancel_subscription</a>() -> ApiResponseCustomerSubscriptionResponse</code></summary>
<dl>
<dd>

#### 📝 Description

<dl>
<dd>

<dl>
<dd>

Cancel the current user's subscription at period end.
</dd>
</dl>
</dd>
</dl>

#### 🔌 Usage

<dl>
<dd>

<dl>
<dd>

```python
from onepin import OnePinClient
from onepin.environment import OnePinClientEnvironment

client = OnePinClient(
    token="<token>",
    environment=OnePinClientEnvironment.PROD,
)

client.users.cancel_subscription()

```
</dd>
</dl>
</dd>
</dl>

#### ⚙️ Parameters

<dl>
<dd>

<dl>
<dd>

**request_options:** `typing.Optional[RequestOptions]` — Request-specific configuration.
    
</dd>
</dl>
</dd>
</dl>


</dd>
</dl>
</details>

<details><summary><code>client.users.<a href="src/onepin/users/client.py">change_plan</a>(...) -> ApiResponseCustomerSubscriptionResponse</code></summary>
<dl>
<dd>

#### 📝 Description

<dl>
<dd>

<dl>
<dd>

Switch the current user's subscription to a different plan.
</dd>
</dl>
</dd>
</dl>

#### 🔌 Usage

<dl>
<dd>

<dl>
<dd>

```python
from onepin import OnePinClient
from onepin.environment import OnePinClientEnvironment

client = OnePinClient(
    token="<token>",
    environment=OnePinClientEnvironment.PROD,
)

client.users.change_plan(
    new_plan_id="new_plan_id",
)

```
</dd>
</dl>
</dd>
</dl>

#### ⚙️ Parameters

<dl>
<dd>

<dl>
<dd>

**new_plan_id:** `str` 
    
</dd>
</dl>

<dl>
<dd>

**request_options:** `typing.Optional[RequestOptions]` — Request-specific configuration.
    
</dd>
</dl>
</dd>
</dl>


</dd>
</dl>
</details>

<details><summary><code>client.users.<a href="src/onepin/users/client.py">cancel_scheduled_change</a>() -> ApiResponseCustomerSubscriptionResponse</code></summary>
<dl>
<dd>

#### 📝 Description

<dl>
<dd>

<dl>
<dd>

Cancel a scheduled plan downgrade.
</dd>
</dl>
</dd>
</dl>

#### 🔌 Usage

<dl>
<dd>

<dl>
<dd>

```python
from onepin import OnePinClient
from onepin.environment import OnePinClientEnvironment

client = OnePinClient(
    token="<token>",
    environment=OnePinClientEnvironment.PROD,
)

client.users.cancel_scheduled_change()

```
</dd>
</dl>
</dd>
</dl>

#### ⚙️ Parameters

<dl>
<dd>

<dl>
<dd>

**request_options:** `typing.Optional[RequestOptions]` — Request-specific configuration.
    
</dd>
</dl>
</dd>
</dl>


</dd>
</dl>
</details>

<details><summary><code>client.users.<a href="src/onepin/users/client.py">list_payment_methods</a>() -> ApiResponseListPaymentMethodResponse</code></summary>
<dl>
<dd>

#### 📝 Description

<dl>
<dd>

<dl>
<dd>

List the current user's saved payment methods.
</dd>
</dl>
</dd>
</dl>

#### 🔌 Usage

<dl>
<dd>

<dl>
<dd>

```python
from onepin import OnePinClient
from onepin.environment import OnePinClientEnvironment

client = OnePinClient(
    token="<token>",
    environment=OnePinClientEnvironment.PROD,
)

client.users.list_payment_methods()

```
</dd>
</dl>
</dd>
</dl>

#### ⚙️ Parameters

<dl>
<dd>

<dl>
<dd>

**request_options:** `typing.Optional[RequestOptions]` — Request-specific configuration.
    
</dd>
</dl>
</dd>
</dl>


</dd>
</dl>
</details>

<details><summary><code>client.users.<a href="src/onepin/users/client.py">add_payment_method</a>() -> ApiResponseSetupIntentResponse</code></summary>
<dl>
<dd>

#### 📝 Description

<dl>
<dd>

<dl>
<dd>

Create a Stripe SetupIntent to add a new payment method.
</dd>
</dl>
</dd>
</dl>

#### 🔌 Usage

<dl>
<dd>

<dl>
<dd>

```python
from onepin import OnePinClient
from onepin.environment import OnePinClientEnvironment

client = OnePinClient(
    token="<token>",
    environment=OnePinClientEnvironment.PROD,
)

client.users.add_payment_method()

```
</dd>
</dl>
</dd>
</dl>

#### ⚙️ Parameters

<dl>
<dd>

<dl>
<dd>

**request_options:** `typing.Optional[RequestOptions]` — Request-specific configuration.
    
</dd>
</dl>
</dd>
</dl>


</dd>
</dl>
</details>

<details><summary><code>client.users.<a href="src/onepin/users/client.py">delete_payment_method</a>(...) -> ApiResponseDict</code></summary>
<dl>
<dd>

#### 📝 Description

<dl>
<dd>

<dl>
<dd>

Detach a payment method from the current user's account.
</dd>
</dl>
</dd>
</dl>

#### 🔌 Usage

<dl>
<dd>

<dl>
<dd>

```python
from onepin import OnePinClient
from onepin.environment import OnePinClientEnvironment

client = OnePinClient(
    token="<token>",
    environment=OnePinClientEnvironment.PROD,
)

client.users.delete_payment_method(
    payment_method_id="payment_method_id",
)

```
</dd>
</dl>
</dd>
</dl>

#### ⚙️ Parameters

<dl>
<dd>

<dl>
<dd>

**payment_method_id:** `str` 
    
</dd>
</dl>

<dl>
<dd>

**request_options:** `typing.Optional[RequestOptions]` — Request-specific configuration.
    
</dd>
</dl>
</dd>
</dl>


</dd>
</dl>
</details>

<details><summary><code>client.users.<a href="src/onepin/users/client.py">set_default_payment_method</a>(...) -> ApiResponseDict</code></summary>
<dl>
<dd>

#### 📝 Description

<dl>
<dd>

<dl>
<dd>

Set a payment method as the default for the current user.
</dd>
</dl>
</dd>
</dl>

#### 🔌 Usage

<dl>
<dd>

<dl>
<dd>

```python
from onepin import OnePinClient
from onepin.environment import OnePinClientEnvironment

client = OnePinClient(
    token="<token>",
    environment=OnePinClientEnvironment.PROD,
)

client.users.set_default_payment_method(
    payment_method_id="payment_method_id",
)

```
</dd>
</dl>
</dd>
</dl>

#### ⚙️ Parameters

<dl>
<dd>

<dl>
<dd>

**payment_method_id:** `str` 
    
</dd>
</dl>

<dl>
<dd>

**request_options:** `typing.Optional[RequestOptions]` — Request-specific configuration.
    
</dd>
</dl>
</dd>
</dl>


</dd>
</dl>
</details>

<details><summary><code>client.users.<a href="src/onepin/users/client.py">get_my_credits</a>() -> ApiResponseBalanceResponse</code></summary>
<dl>
<dd>

#### 📝 Description

<dl>
<dd>

<dl>
<dd>

Return the current user's credit balance + monthly grant + period anchor.

Free-tier users have no Subscription row; the response falls back to the
canonical FREE Plan (1000 credits/mo, calendar-month boundary).
</dd>
</dl>
</dd>
</dl>

#### 🔌 Usage

<dl>
<dd>

<dl>
<dd>

```python
from onepin import OnePinClient
from onepin.environment import OnePinClientEnvironment

client = OnePinClient(
    token="<token>",
    environment=OnePinClientEnvironment.PROD,
)

client.users.get_my_credits()

```
</dd>
</dl>
</dd>
</dl>

#### ⚙️ Parameters

<dl>
<dd>

<dl>
<dd>

**request_options:** `typing.Optional[RequestOptions]` — Request-specific configuration.
    
</dd>
</dl>
</dd>
</dl>


</dd>
</dl>
</details>

<details><summary><code>client.users.<a href="src/onepin/users/client.py">get_my_plan_limits</a>() -> ApiResponsePlanLimits</code></summary>
<dl>
<dd>

#### 📝 Description

<dl>
<dd>

<dl>
<dd>

Return the typed plan limits for the current user (FE plan-card UI consumer).
</dd>
</dl>
</dd>
</dl>

#### 🔌 Usage

<dl>
<dd>

<dl>
<dd>

```python
from onepin import OnePinClient
from onepin.environment import OnePinClientEnvironment

client = OnePinClient(
    token="<token>",
    environment=OnePinClientEnvironment.PROD,
)

client.users.get_my_plan_limits()

```
</dd>
</dl>
</dd>
</dl>

#### ⚙️ Parameters

<dl>
<dd>

<dl>
<dd>

**request_options:** `typing.Optional[RequestOptions]` — Request-specific configuration.
    
</dd>
</dl>
</dd>
</dl>


</dd>
</dl>
</details>

<details><summary><code>client.users.<a href="src/onepin/users/client.py">list_invoices</a>(...) -> ApiResponseInvoiceListResponse</code></summary>
<dl>
<dd>

#### 📝 Description

<dl>
<dd>

<dl>
<dd>

List invoices for the current user.
</dd>
</dl>
</dd>
</dl>

#### 🔌 Usage

<dl>
<dd>

<dl>
<dd>

```python
from onepin import OnePinClient
from onepin.environment import OnePinClientEnvironment

client = OnePinClient(
    token="<token>",
    environment=OnePinClientEnvironment.PROD,
)

client.users.list_invoices()

```
</dd>
</dl>
</dd>
</dl>

#### ⚙️ Parameters

<dl>
<dd>

<dl>
<dd>

**limit:** `typing.Optional[int]` 
    
</dd>
</dl>

<dl>
<dd>

**starting_after:** `typing.Optional[str]` 
    
</dd>
</dl>

<dl>
<dd>

**request_options:** `typing.Optional[RequestOptions]` — Request-specific configuration.
    
</dd>
</dl>
</dd>
</dl>


</dd>
</dl>
</details>

<details><summary><code>client.users.<a href="src/onepin/users/client.py">get_current_notification_preferences</a>() -> ApiResponseEmailNotificationPreferencesOut</code></summary>
<dl>
<dd>

#### 📝 Description

<dl>
<dd>

<dl>
<dd>

Get the current user's email notification preferences.
</dd>
</dl>
</dd>
</dl>

#### 🔌 Usage

<dl>
<dd>

<dl>
<dd>

```python
from onepin import OnePinClient
from onepin.environment import OnePinClientEnvironment

client = OnePinClient(
    token="<token>",
    environment=OnePinClientEnvironment.PROD,
)

client.users.get_current_notification_preferences()

```
</dd>
</dl>
</dd>
</dl>

#### ⚙️ Parameters

<dl>
<dd>

<dl>
<dd>

**request_options:** `typing.Optional[RequestOptions]` — Request-specific configuration.
    
</dd>
</dl>
</dd>
</dl>


</dd>
</dl>
</details>

<details><summary><code>client.users.<a href="src/onepin/users/client.py">update_current_notification_preferences</a>(...) -> ApiResponseEmailNotificationPreferencesOut</code></summary>
<dl>
<dd>

#### 📝 Description

<dl>
<dd>

<dl>
<dd>

Partially update the current user's email notification preferences.
</dd>
</dl>
</dd>
</dl>

#### 🔌 Usage

<dl>
<dd>

<dl>
<dd>

```python
from onepin import OnePinClient
from onepin.environment import OnePinClientEnvironment

client = OnePinClient(
    token="<token>",
    environment=OnePinClientEnvironment.PROD,
)

client.users.update_current_notification_preferences()

```
</dd>
</dl>
</dd>
</dl>

#### ⚙️ Parameters

<dl>
<dd>

<dl>
<dd>

**completed_generation_email:** `typing.Optional[bool]` 
    
</dd>
</dl>

<dl>
<dd>

**weekly_usage_summary_email:** `typing.Optional[bool]` 
    
</dd>
</dl>

<dl>
<dd>

**product_updates_email:** `typing.Optional[bool]` 
    
</dd>
</dl>

<dl>
<dd>

**request_options:** `typing.Optional[RequestOptions]` — Request-specific configuration.
    
</dd>
</dl>
</dd>
</dl>


</dd>
</dl>
</details>

<details><summary><code>client.users.<a href="src/onepin/users/client.py">list_my_templates</a>(...) -> ApiListResponseTemplateOut</code></summary>
<dl>
<dd>

#### 📝 Description

<dl>
<dd>

<dl>
<dd>

List templates the current user created in the current workspace.

Scoped on both `(workspace_id, created_by)` so when workspaces become
multi-user this endpoint keeps returning only the caller's own rows —
other workspace members' public/starter templates surface via the
gallery endpoint (`GET /api/v1/templates`) instead.
</dd>
</dl>
</dd>
</dl>

#### 🔌 Usage

<dl>
<dd>

<dl>
<dd>

```python
from onepin import OnePinClient
from onepin.environment import OnePinClientEnvironment

client = OnePinClient(
    token="<token>",
    environment=OnePinClientEnvironment.PROD,
)

client.users.list_my_templates()

```
</dd>
</dl>
</dd>
</dl>

#### ⚙️ Parameters

<dl>
<dd>

<dl>
<dd>

**category:** `typing.Optional[typing.List[TemplateCategory]]` — Repeat for OR, e.g. ?category=media&category=creative
    
</dd>
</dl>

<dl>
<dd>

**search:** `typing.Optional[str]` 
    
</dd>
</dl>

<dl>
<dd>

**sort:** `typing.Optional[ListMyTemplatesApiV1UsersMeTemplatesGetRequestSort]` 
    
</dd>
</dl>

<dl>
<dd>

**offset:** `typing.Optional[int]` 
    
</dd>
</dl>

<dl>
<dd>

**limit:** `typing.Optional[int]` 
    
</dd>
</dl>

<dl>
<dd>

**favorites_only:** `typing.Optional[bool]` 
    
</dd>
</dl>

<dl>
<dd>

**workspace_id:** `typing.Optional[str]` 
    
</dd>
</dl>

<dl>
<dd>

**request_options:** `typing.Optional[RequestOptions]` — Request-specific configuration.
    
</dd>
</dl>
</dd>
</dl>


</dd>
</dl>
</details>

## workflows
<details><summary><code>client.workflows.<a href="src/onepin/workflows/client.py">list</a>(...) -> ApiCountedListResponseWorkflowListItem</code></summary>
<dl>
<dd>

#### 📝 Description

<dl>
<dd>

<dl>
<dd>

List workflows in the current workspace.

Multi-sort: `sort` and `order` are parallel lists.
`?sort=runs_count&sort=name&order=desc&order=asc` orders primarily by
runs_count DESC, secondarily by name ASC. When `order` is shorter than
`sort`, missing entries default per-field:
`name=asc, updated_at=desc, runs_count=desc`. When `sort` is omitted,
list defaults to `updated_at DESC`. Every sort path appends
`Workflow.id ASC` as a deterministic tiebreaker for pagination stability.

`paused` is accepted but currently returns an empty result because
backend pause state is not implemented. `last_run_status` is the raw
RunStatus value, including values like `pending` or `cancelled`, and
pagination `total` is the filtered total for the current query.
</dd>
</dl>
</dd>
</dl>

#### 🔌 Usage

<dl>
<dd>

<dl>
<dd>

```python
from onepin import OnePinClient
from onepin.environment import OnePinClientEnvironment

client = OnePinClient(
    token="<token>",
    environment=OnePinClientEnvironment.PROD,
)

client.workflows.list()

```
</dd>
</dl>
</dd>
</dl>

#### ⚙️ Parameters

<dl>
<dd>

<dl>
<dd>

**status:** `typing.Optional[WorkflowListStatus]` — UI workflow status filter. `paused` is accepted for forward compatibility and currently returns no rows.
    
</dd>
</dl>

<dl>
<dd>

**search:** `typing.Optional[str]` — Case-insensitive search over name and description.
    
</dd>
</dl>

<dl>
<dd>

**sort:** `typing.Optional[typing.List[ListWorkflowsRequestSortItem]]` — Repeat for multi-sort. Pairs with `order` index-wise.
    
</dd>
</dl>

<dl>
<dd>

**order:** `typing.Optional[typing.List[ListWorkflowsRequestOrderItem]]` — Parallel to sort[]; shorter is padded with per-field defaults.
    
</dd>
</dl>

<dl>
<dd>

**last_run_after:** `typing.Optional[datetime.datetime]` — Filter workflows whose last_run_at is at or after this ISO datetime.
    
</dd>
</dl>

<dl>
<dd>

**last_run_before:** `typing.Optional[datetime.datetime]` — Filter workflows whose last_run_at is at or before this ISO datetime.
    
</dd>
</dl>

<dl>
<dd>

**offset:** `typing.Optional[int]` 
    
</dd>
</dl>

<dl>
<dd>

**limit:** `typing.Optional[int]` 
    
</dd>
</dl>

<dl>
<dd>

**workspace_id:** `typing.Optional[str]` 
    
</dd>
</dl>

<dl>
<dd>

**request_options:** `typing.Optional[RequestOptions]` — Request-specific configuration.
    
</dd>
</dl>
</dd>
</dl>


</dd>
</dl>
</details>

<details><summary><code>client.workflows.<a href="src/onepin/workflows/client.py">create_workflow</a>(...) -> ApiResponseWorkflowOut</code></summary>
<dl>
<dd>

#### 📝 Description

<dl>
<dd>

<dl>
<dd>

Create a workflow.
</dd>
</dl>
</dd>
</dl>

#### 🔌 Usage

<dl>
<dd>

<dl>
<dd>

```python
from onepin import OnePinClient
from onepin.environment import OnePinClientEnvironment

client = OnePinClient(
    token="<token>",
    environment=OnePinClientEnvironment.PROD,
)

client.workflows.create_workflow(
    name="name",
)

```
</dd>
</dl>
</dd>
</dl>

#### ⚙️ Parameters

<dl>
<dd>

<dl>
<dd>

**name:** `str` 
    
</dd>
</dl>

<dl>
<dd>

**workspace_id:** `typing.Optional[str]` 
    
</dd>
</dl>

<dl>
<dd>

**description:** `typing.Optional[str]` 
    
</dd>
</dl>

<dl>
<dd>

**definition:** `typing.Optional[WorkflowDefinitionInput]` 
    
</dd>
</dl>

<dl>
<dd>

**request_options:** `typing.Optional[RequestOptions]` — Request-specific configuration.
    
</dd>
</dl>
</dd>
</dl>


</dd>
</dl>
</details>

<details><summary><code>client.workflows.<a href="src/onepin/workflows/client.py">get</a>(...) -> ApiResponseWorkflowOut</code></summary>
<dl>
<dd>

#### 📝 Description

<dl>
<dd>

<dl>
<dd>

Fetch a workflow by id.
</dd>
</dl>
</dd>
</dl>

#### 🔌 Usage

<dl>
<dd>

<dl>
<dd>

```python
from onepin import OnePinClient
from onepin.environment import OnePinClientEnvironment

client = OnePinClient(
    token="<token>",
    environment=OnePinClientEnvironment.PROD,
)

client.workflows.get(
    workflow_id="workflow_id",
)

```
</dd>
</dl>
</dd>
</dl>

#### ⚙️ Parameters

<dl>
<dd>

<dl>
<dd>

**workflow_id:** `str` 
    
</dd>
</dl>

<dl>
<dd>

**workspace_id:** `typing.Optional[str]` 
    
</dd>
</dl>

<dl>
<dd>

**request_options:** `typing.Optional[RequestOptions]` — Request-specific configuration.
    
</dd>
</dl>
</dd>
</dl>


</dd>
</dl>
</details>

<details><summary><code>client.workflows.<a href="src/onepin/workflows/client.py">update_workflow</a>(...) -> ApiResponseWorkflowOut</code></summary>
<dl>
<dd>

#### 📝 Description

<dl>
<dd>

<dl>
<dd>

Update a workflow.
</dd>
</dl>
</dd>
</dl>

#### 🔌 Usage

<dl>
<dd>

<dl>
<dd>

```python
from onepin import OnePinClient, WorkflowDefinitionInput
from onepin.environment import OnePinClientEnvironment

client = OnePinClient(
    token="<token>",
    environment=OnePinClientEnvironment.PROD,
)

client.workflows.update_workflow(
    workflow_id="workflow_id",
    name="name",
    definition=WorkflowDefinitionInput(),
)

```
</dd>
</dl>
</dd>
</dl>

#### ⚙️ Parameters

<dl>
<dd>

<dl>
<dd>

**workflow_id:** `str` 
    
</dd>
</dl>

<dl>
<dd>

**name:** `str` 
    
</dd>
</dl>

<dl>
<dd>

**definition:** `WorkflowDefinitionInput` 
    
</dd>
</dl>

<dl>
<dd>

**workspace_id:** `typing.Optional[str]` 
    
</dd>
</dl>

<dl>
<dd>

**description:** `typing.Optional[str]` 
    
</dd>
</dl>

<dl>
<dd>

**request_options:** `typing.Optional[RequestOptions]` — Request-specific configuration.
    
</dd>
</dl>
</dd>
</dl>


</dd>
</dl>
</details>

<details><summary><code>client.workflows.<a href="src/onepin/workflows/client.py">delete_workflow</a>(...) -> ApiResponseDict</code></summary>
<dl>
<dd>

#### 📝 Description

<dl>
<dd>

<dl>
<dd>

Soft-delete a workflow.
</dd>
</dl>
</dd>
</dl>

#### 🔌 Usage

<dl>
<dd>

<dl>
<dd>

```python
from onepin import OnePinClient
from onepin.environment import OnePinClientEnvironment

client = OnePinClient(
    token="<token>",
    environment=OnePinClientEnvironment.PROD,
)

client.workflows.delete_workflow(
    workflow_id="workflow_id",
)

```
</dd>
</dl>
</dd>
</dl>

#### ⚙️ Parameters

<dl>
<dd>

<dl>
<dd>

**workflow_id:** `str` 
    
</dd>
</dl>

<dl>
<dd>

**workspace_id:** `typing.Optional[str]` 
    
</dd>
</dl>

<dl>
<dd>

**request_options:** `typing.Optional[RequestOptions]` — Request-specific configuration.
    
</dd>
</dl>
</dd>
</dl>


</dd>
</dl>
</details>

<details><summary><code>client.workflows.<a href="src/onepin/workflows/client.py">patch_workflow</a>(...) -> ApiResponseWorkflowOut</code></summary>
<dl>
<dd>

#### 📝 Description

<dl>
<dd>

<dl>
<dd>

Partially update a workflow. Only fields present in the body are applied.
</dd>
</dl>
</dd>
</dl>

#### 🔌 Usage

<dl>
<dd>

<dl>
<dd>

```python
from onepin import OnePinClient
from onepin.environment import OnePinClientEnvironment

client = OnePinClient(
    token="<token>",
    environment=OnePinClientEnvironment.PROD,
)

client.workflows.patch_workflow(
    workflow_id="workflow_id",
)

```
</dd>
</dl>
</dd>
</dl>

#### ⚙️ Parameters

<dl>
<dd>

<dl>
<dd>

**workflow_id:** `str` 
    
</dd>
</dl>

<dl>
<dd>

**workspace_id:** `typing.Optional[str]` 
    
</dd>
</dl>

<dl>
<dd>

**name:** `typing.Optional[str]` 
    
</dd>
</dl>

<dl>
<dd>

**description:** `typing.Optional[str]` 
    
</dd>
</dl>

<dl>
<dd>

**definition:** `typing.Optional[WorkflowDefinitionInput]` 
    
</dd>
</dl>

<dl>
<dd>

**request_options:** `typing.Optional[RequestOptions]` — Request-specific configuration.
    
</dd>
</dl>
</dd>
</dl>


</dd>
</dl>
</details>

<details><summary><code>client.workflows.<a href="src/onepin/workflows/client.py">list_workflow_uploads</a>(...) -> ApiListResponseUploadOut</code></summary>
<dl>
<dd>

#### 📝 Description

<dl>
<dd>

<dl>
<dd>

List confirmed uploads attached to a workflow.
</dd>
</dl>
</dd>
</dl>

#### 🔌 Usage

<dl>
<dd>

<dl>
<dd>

```python
from onepin import OnePinClient
from onepin.environment import OnePinClientEnvironment

client = OnePinClient(
    token="<token>",
    environment=OnePinClientEnvironment.PROD,
)

client.workflows.list_workflow_uploads(
    workflow_id="workflow_id",
)

```
</dd>
</dl>
</dd>
</dl>

#### ⚙️ Parameters

<dl>
<dd>

<dl>
<dd>

**workflow_id:** `str` 
    
</dd>
</dl>

<dl>
<dd>

**offset:** `typing.Optional[int]` 
    
</dd>
</dl>

<dl>
<dd>

**limit:** `typing.Optional[int]` 
    
</dd>
</dl>

<dl>
<dd>

**workspace_id:** `typing.Optional[str]` 
    
</dd>
</dl>

<dl>
<dd>

**request_options:** `typing.Optional[RequestOptions]` — Request-specific configuration.
    
</dd>
</dl>
</dd>
</dl>


</dd>
</dl>
</details>

<details><summary><code>client.workflows.<a href="src/onepin/workflows/client.py">estimate_workflow</a>(...) -> ApiResponseEstimateResponse</code></summary>
<dl>
<dd>

#### 📝 Description

<dl>
<dd>

<dl>
<dd>

Estimate workflow credits without creating a run.
</dd>
</dl>
</dd>
</dl>

#### 🔌 Usage

<dl>
<dd>

<dl>
<dd>

```python
from onepin import OnePinClient
from onepin.environment import OnePinClientEnvironment

client = OnePinClient(
    token="<token>",
    environment=OnePinClientEnvironment.PROD,
)

client.workflows.estimate_workflow(
    workflow_id="workflow_id",
)

```
</dd>
</dl>
</dd>
</dl>

#### ⚙️ Parameters

<dl>
<dd>

<dl>
<dd>

**workflow_id:** `str` 
    
</dd>
</dl>

<dl>
<dd>

**workspace_id:** `typing.Optional[str]` 
    
</dd>
</dl>

<dl>
<dd>

**request_options:** `typing.Optional[RequestOptions]` — Request-specific configuration.
    
</dd>
</dl>
</dd>
</dl>


</dd>
</dl>
</details>

<details><summary><code>client.workflows.<a href="src/onepin/workflows/client.py">preview_run</a>(...) -> ApiResponseEstimateResponse</code></summary>
<dl>
<dd>

#### 📝 Description

<dl>
<dd>

<dl>
<dd>

Estimate workflow run credits without creating a run.
</dd>
</dl>
</dd>
</dl>

#### 🔌 Usage

<dl>
<dd>

<dl>
<dd>

```python
from onepin import OnePinClient
from onepin.environment import OnePinClientEnvironment

client = OnePinClient(
    token="<token>",
    environment=OnePinClientEnvironment.PROD,
)

client.workflows.preview_run(
    workflow_id="workflow_id",
)

```
</dd>
</dl>
</dd>
</dl>

#### ⚙️ Parameters

<dl>
<dd>

<dl>
<dd>

**workflow_id:** `str` 
    
</dd>
</dl>

<dl>
<dd>

**workspace_id:** `typing.Optional[str]` 
    
</dd>
</dl>

<dl>
<dd>

**request_options:** `typing.Optional[RequestOptions]` — Request-specific configuration.
    
</dd>
</dl>
</dd>
</dl>


</dd>
</dl>
</details>

<details><summary><code>client.workflows.<a href="src/onepin/workflows/client.py">runs_summary</a>(...) -> ApiResponseRunsSummaryOut</code></summary>
<dl>
<dd>

#### 📝 Description

<dl>
<dd>

<dl>
<dd>

Aggregate run-status counts plus pass_rate and average_duration_seconds.

``pass_rate = completed / (completed + failed + cancelled)``;
``None`` when no terminal runs.
``average_duration_seconds = mean(completed_at - started_at)`` over
completed runs only; ``None`` when there are zero completed runs.
</dd>
</dl>
</dd>
</dl>

#### 🔌 Usage

<dl>
<dd>

<dl>
<dd>

```python
from onepin import OnePinClient
from onepin.environment import OnePinClientEnvironment

client = OnePinClient(
    token="<token>",
    environment=OnePinClientEnvironment.PROD,
)

client.workflows.runs_summary(
    workflow_id="workflow_id",
)

```
</dd>
</dl>
</dd>
</dl>

#### ⚙️ Parameters

<dl>
<dd>

<dl>
<dd>

**workflow_id:** `str` 
    
</dd>
</dl>

<dl>
<dd>

**from:** `typing.Optional[datetime.datetime]` — Filter runs by created_at >= this ISO datetime.
    
</dd>
</dl>

<dl>
<dd>

**to:** `typing.Optional[datetime.datetime]` — Filter runs by created_at <= this ISO datetime.
    
</dd>
</dl>

<dl>
<dd>

**workspace_id:** `typing.Optional[str]` 
    
</dd>
</dl>

<dl>
<dd>

**request_options:** `typing.Optional[RequestOptions]` — Request-specific configuration.
    
</dd>
</dl>
</dd>
</dl>


</dd>
</dl>
</details>

<details><summary><code>client.workflows.<a href="src/onepin/workflows/client.py">get_run_steps</a>(...) -> ApiResponseListWorkflowRunStepOut</code></summary>
<dl>
<dd>

#### 📝 Description

<dl>
<dd>

<dl>
<dd>

List steps for a workflow run.
</dd>
</dl>
</dd>
</dl>

#### 🔌 Usage

<dl>
<dd>

<dl>
<dd>

```python
from onepin import OnePinClient
from onepin.environment import OnePinClientEnvironment

client = OnePinClient(
    token="<token>",
    environment=OnePinClientEnvironment.PROD,
)

client.workflows.get_run_steps(
    workflow_id="workflow_id",
    run_id="run_id",
)

```
</dd>
</dl>
</dd>
</dl>

#### ⚙️ Parameters

<dl>
<dd>

<dl>
<dd>

**workflow_id:** `str` 
    
</dd>
</dl>

<dl>
<dd>

**run_id:** `str` 
    
</dd>
</dl>

<dl>
<dd>

**workspace_id:** `typing.Optional[str]` 
    
</dd>
</dl>

<dl>
<dd>

**request_options:** `typing.Optional[RequestOptions]` — Request-specific configuration.
    
</dd>
</dl>
</dd>
</dl>


</dd>
</dl>
</details>

<details><summary><code>client.workflows.<a href="src/onepin/workflows/client.py">get_run_overview</a>(...) -> ApiResponseWorkflowRunOverviewOut</code></summary>
<dl>
<dd>

#### 📝 Description

<dl>
<dd>

<dl>
<dd>

Fetch server-computed overview aggregates for a workflow run.
</dd>
</dl>
</dd>
</dl>

#### 🔌 Usage

<dl>
<dd>

<dl>
<dd>

```python
from onepin import OnePinClient
from onepin.environment import OnePinClientEnvironment

client = OnePinClient(
    token="<token>",
    environment=OnePinClientEnvironment.PROD,
)

client.workflows.get_run_overview(
    workflow_id="workflow_id",
    run_id="run_id",
)

```
</dd>
</dl>
</dd>
</dl>

#### ⚙️ Parameters

<dl>
<dd>

<dl>
<dd>

**workflow_id:** `str` 
    
</dd>
</dl>

<dl>
<dd>

**run_id:** `str` 
    
</dd>
</dl>

<dl>
<dd>

**workspace_id:** `typing.Optional[str]` 
    
</dd>
</dl>

<dl>
<dd>

**request_options:** `typing.Optional[RequestOptions]` — Request-specific configuration.
    
</dd>
</dl>
</dd>
</dl>


</dd>
</dl>
</details>

<details><summary><code>client.workflows.<a href="src/onepin/workflows/client.py">get_run_data</a>(...) -> WorkflowRunDataResponse</code></summary>
<dl>
<dd>

#### 📝 Description

<dl>
<dd>

<dl>
<dd>

Fetch normalized grouped rows/cards for the run detail Data tab.

`pagination.total` is search-scoped and language-independent; language
filters only card lists, so returned rows may contain empty `cards`.
</dd>
</dl>
</dd>
</dl>

#### 🔌 Usage

<dl>
<dd>

<dl>
<dd>

```python
from onepin import OnePinClient
from onepin.environment import OnePinClientEnvironment

client = OnePinClient(
    token="<token>",
    environment=OnePinClientEnvironment.PROD,
)

client.workflows.get_run_data(
    workflow_id="workflow_id",
    run_id="run_id",
)

```
</dd>
</dl>
</dd>
</dl>

#### ⚙️ Parameters

<dl>
<dd>

<dl>
<dd>

**workflow_id:** `str` 
    
</dd>
</dl>

<dl>
<dd>

**run_id:** `str` 
    
</dd>
</dl>

<dl>
<dd>

**search:** `typing.Optional[str]` — Case-insensitive search over visible grouped source/script text.
    
</dd>
</dl>

<dl>
<dd>

**language:** `typing.Optional[str]` — Exact full-locale card filter. `_` is normalized to `-`; filtering cards preserves row visibility and pagination.total remains language-independent, so rows may return empty cards.
    
</dd>
</dl>

<dl>
<dd>

**offset:** `typing.Optional[int]` 
    
</dd>
</dl>

<dl>
<dd>

**limit:** `typing.Optional[int]` 
    
</dd>
</dl>

<dl>
<dd>

**workspace_id:** `typing.Optional[str]` 
    
</dd>
</dl>

<dl>
<dd>

**request_options:** `typing.Optional[RequestOptions]` — Request-specific configuration.
    
</dd>
</dl>
</dd>
</dl>


</dd>
</dl>
</details>

<details><summary><code>client.workflows.<a href="src/onepin/workflows/client.py">download_run</a>(...) -> ApiResponseDownloadUrlOut</code></summary>
<dl>
<dd>

#### 📝 Description

<dl>
<dd>

<dl>
<dd>

Create a temporary download URL for a workflow run export.
</dd>
</dl>
</dd>
</dl>

#### 🔌 Usage

<dl>
<dd>

<dl>
<dd>

```python
from onepin import OnePinClient
from onepin.environment import OnePinClientEnvironment

client = OnePinClient(
    token="<token>",
    environment=OnePinClientEnvironment.PROD,
)

client.workflows.download_run(
    workflow_id="workflow_id",
    run_id="run_id",
)

```
</dd>
</dl>
</dd>
</dl>

#### ⚙️ Parameters

<dl>
<dd>

<dl>
<dd>

**workflow_id:** `str` 
    
</dd>
</dl>

<dl>
<dd>

**run_id:** `str` 
    
</dd>
</dl>

<dl>
<dd>

**workspace_id:** `typing.Optional[str]` 
    
</dd>
</dl>

<dl>
<dd>

**request_options:** `typing.Optional[RequestOptions]` — Request-specific configuration.
    
</dd>
</dl>
</dd>
</dl>


</dd>
</dl>
</details>

<details><summary><code>client.workflows.<a href="src/onepin/workflows/client.py">download_run_node</a>(...) -> ApiResponseDownloadUrlOut</code></summary>
<dl>
<dd>

#### 📝 Description

<dl>
<dd>

<dl>
<dd>

Create a temporary download URL for a node-level workflow export.
</dd>
</dl>
</dd>
</dl>

#### 🔌 Usage

<dl>
<dd>

<dl>
<dd>

```python
from onepin import OnePinClient
from onepin.environment import OnePinClientEnvironment

client = OnePinClient(
    token="<token>",
    environment=OnePinClientEnvironment.PROD,
)

client.workflows.download_run_node(
    workflow_id="workflow_id",
    run_id="run_id",
    node_id="node_id",
)

```
</dd>
</dl>
</dd>
</dl>

#### ⚙️ Parameters

<dl>
<dd>

<dl>
<dd>

**workflow_id:** `str` 
    
</dd>
</dl>

<dl>
<dd>

**run_id:** `str` 
    
</dd>
</dl>

<dl>
<dd>

**node_id:** `str` 
    
</dd>
</dl>

<dl>
<dd>

**workspace_id:** `typing.Optional[str]` 
    
</dd>
</dl>

<dl>
<dd>

**request_options:** `typing.Optional[RequestOptions]` — Request-specific configuration.
    
</dd>
</dl>
</dd>
</dl>


</dd>
</dl>
</details>

<details><summary><code>client.workflows.<a href="src/onepin/workflows/client.py">duplicate_workflow</a>(...) -> ApiResponseWorkflowOut</code></summary>
<dl>
<dd>

#### 📝 Description

<dl>
<dd>

<dl>
<dd>

Duplicate a workflow.
</dd>
</dl>
</dd>
</dl>

#### 🔌 Usage

<dl>
<dd>

<dl>
<dd>

```python
from onepin import OnePinClient
from onepin.environment import OnePinClientEnvironment

client = OnePinClient(
    token="<token>",
    environment=OnePinClientEnvironment.PROD,
)

client.workflows.duplicate_workflow(
    workflow_id="workflow_id",
)

```
</dd>
</dl>
</dd>
</dl>

#### ⚙️ Parameters

<dl>
<dd>

<dl>
<dd>

**workflow_id:** `str` 
    
</dd>
</dl>

<dl>
<dd>

**workspace_id:** `typing.Optional[str]` 
    
</dd>
</dl>

<dl>
<dd>

**request_options:** `typing.Optional[RequestOptions]` — Request-specific configuration.
    
</dd>
</dl>
</dd>
</dl>


</dd>
</dl>
</details>

## Workflows Runs
<details><summary><code>client.workflows.runs.<a href="src/onepin/workflows/runs/client.py">list</a>(...) -> ApiCountedListResponseWorkflowRunListItem</code></summary>
<dl>
<dd>

#### 📝 Description

<dl>
<dd>

<dl>
<dd>

List runs for a workflow.

Tiebreaker is always ``id ASC`` so offset/limit pagination is stable when
primary sort keys tie. ``status`` accepts comma-separated raw RunStatus
values; unknown values return 422. ``search`` matches the triggering
user's display name (full name, falling back to email).
</dd>
</dl>
</dd>
</dl>

#### 🔌 Usage

<dl>
<dd>

<dl>
<dd>

```python
from onepin import OnePinClient
from onepin.environment import OnePinClientEnvironment

client = OnePinClient(
    token="<token>",
    environment=OnePinClientEnvironment.PROD,
)

client.workflows.runs.list(
    workflow_id="workflow_id",
)

```
</dd>
</dl>
</dd>
</dl>

#### ⚙️ Parameters

<dl>
<dd>

<dl>
<dd>

**workflow_id:** `str` 
    
</dd>
</dl>

<dl>
<dd>

**offset:** `typing.Optional[int]` 
    
</dd>
</dl>

<dl>
<dd>

**limit:** `typing.Optional[int]` 
    
</dd>
</dl>

<dl>
<dd>

**status:** `typing.Optional[str]` — Comma-separated raw RunStatus values (e.g. `completed,failed`). Values are case-sensitive lowercase. Multiple values OR-match. Empty tokens (e.g. `a,,b`) and unknown values return 422.
    
</dd>
</dl>

<dl>
<dd>

**search:** `typing.Optional[str]` — Case-insensitive search over triggering user's display name and email.
    
</dd>
</dl>

<dl>
<dd>

**sort:** `typing.Optional[ListRunsRequestSort]` — Sort field: created_at | started_at | completed_at | status.
    
</dd>
</dl>

<dl>
<dd>

**order:** `typing.Optional[ListRunsRequestOrder]` — asc or desc.
    
</dd>
</dl>

<dl>
<dd>

**workspace_id:** `typing.Optional[str]` 
    
</dd>
</dl>

<dl>
<dd>

**request_options:** `typing.Optional[RequestOptions]` — Request-specific configuration.
    
</dd>
</dl>
</dd>
</dl>


</dd>
</dl>
</details>

<details><summary><code>client.workflows.runs.<a href="src/onepin/workflows/runs/client.py">start</a>(...) -> ApiResponseWorkflowRunOut</code></summary>
<dl>
<dd>

#### 📝 Description

<dl>
<dd>

<dl>
<dd>

Start a workflow run.
</dd>
</dl>
</dd>
</dl>

#### 🔌 Usage

<dl>
<dd>

<dl>
<dd>

```python
from onepin import OnePinClient
from onepin.environment import OnePinClientEnvironment

client = OnePinClient(
    token="<token>",
    environment=OnePinClientEnvironment.PROD,
)

client.workflows.runs.start(
    workflow_id="workflow_id",
)

```
</dd>
</dl>
</dd>
</dl>

#### ⚙️ Parameters

<dl>
<dd>

<dl>
<dd>

**workflow_id:** `str` 
    
</dd>
</dl>

<dl>
<dd>

**workspace_id:** `typing.Optional[str]` 
    
</dd>
</dl>

<dl>
<dd>

**request_options:** `typing.Optional[RequestOptions]` — Request-specific configuration.
    
</dd>
</dl>
</dd>
</dl>


</dd>
</dl>
</details>

<details><summary><code>client.workflows.runs.<a href="src/onepin/workflows/runs/client.py">get</a>(...) -> ApiResponseWorkflowRunDetailOut</code></summary>
<dl>
<dd>

#### 📝 Description

<dl>
<dd>

<dl>
<dd>

Fetch a workflow run by id.

Includes `definition_snapshot` — the graph/execution config captured
when the run started, returned raw (no config migrations applied) so
it reflects the workflow exactly as it existed for this run.
</dd>
</dl>
</dd>
</dl>

#### 🔌 Usage

<dl>
<dd>

<dl>
<dd>

```python
from onepin import OnePinClient
from onepin.environment import OnePinClientEnvironment

client = OnePinClient(
    token="<token>",
    environment=OnePinClientEnvironment.PROD,
)

client.workflows.runs.get(
    workflow_id="workflow_id",
    run_id="run_id",
)

```
</dd>
</dl>
</dd>
</dl>

#### ⚙️ Parameters

<dl>
<dd>

<dl>
<dd>

**workflow_id:** `str` 
    
</dd>
</dl>

<dl>
<dd>

**run_id:** `str` 
    
</dd>
</dl>

<dl>
<dd>

**workspace_id:** `typing.Optional[str]` 
    
</dd>
</dl>

<dl>
<dd>

**request_options:** `typing.Optional[RequestOptions]` — Request-specific configuration.
    
</dd>
</dl>
</dd>
</dl>


</dd>
</dl>
</details>

<details><summary><code>client.workflows.runs.<a href="src/onepin/workflows/runs/client.py">status</a>(...) -> ApiResponseWorkflowRunStatusOut</code></summary>
<dl>
<dd>

#### 📝 Description

<dl>
<dd>

<dl>
<dd>

Lightweight run status for polling.

Returns only the volatile run state (status, step counts, timestamps,
usage_summary, error, has_export) — no graph snapshot. Use this for
progress polling; call `GET /runs/{run_id}` once to load the immutable
definition snapshot.
</dd>
</dl>
</dd>
</dl>

#### 🔌 Usage

<dl>
<dd>

<dl>
<dd>

```python
from onepin import OnePinClient
from onepin.environment import OnePinClientEnvironment

client = OnePinClient(
    token="<token>",
    environment=OnePinClientEnvironment.PROD,
)

client.workflows.runs.status(
    workflow_id="workflow_id",
    run_id="run_id",
)

```
</dd>
</dl>
</dd>
</dl>

#### ⚙️ Parameters

<dl>
<dd>

<dl>
<dd>

**workflow_id:** `str` 
    
</dd>
</dl>

<dl>
<dd>

**run_id:** `str` 
    
</dd>
</dl>

<dl>
<dd>

**workspace_id:** `typing.Optional[str]` 
    
</dd>
</dl>

<dl>
<dd>

**request_options:** `typing.Optional[RequestOptions]` — Request-specific configuration.
    
</dd>
</dl>
</dd>
</dl>


</dd>
</dl>
</details>

<details><summary><code>client.workflows.runs.<a href="src/onepin/workflows/runs/client.py">cancel</a>(...) -> ApiResponseWorkflowRunOut</code></summary>
<dl>
<dd>

#### 📝 Description

<dl>
<dd>

<dl>
<dd>

Cancel a running workflow run.
</dd>
</dl>
</dd>
</dl>

#### 🔌 Usage

<dl>
<dd>

<dl>
<dd>

```python
from onepin import OnePinClient
from onepin.environment import OnePinClientEnvironment

client = OnePinClient(
    token="<token>",
    environment=OnePinClientEnvironment.PROD,
)

client.workflows.runs.cancel(
    workflow_id="workflow_id",
    run_id="run_id",
)

```
</dd>
</dl>
</dd>
</dl>

#### ⚙️ Parameters

<dl>
<dd>

<dl>
<dd>

**workflow_id:** `str` 
    
</dd>
</dl>

<dl>
<dd>

**run_id:** `str` 
    
</dd>
</dl>

<dl>
<dd>

**workspace_id:** `typing.Optional[str]` 
    
</dd>
</dl>

<dl>
<dd>

**request_options:** `typing.Optional[RequestOptions]` — Request-specific configuration.
    
</dd>
</dl>
</dd>
</dl>


</dd>
</dl>
</details>

