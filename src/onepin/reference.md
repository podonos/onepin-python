# Reference
## auth
<details><summary><code>client.auth.<a href="src/onepin/auth/client.py">whoami</a>() -> ApiResponseAuthWhoamiOut</code></summary>
<dl>
<dd>

#### 📝 Description

<dl>
<dd>

<dl>
<dd>

Return the resolved authentication context for the current credential.

Useful for verifying that a Bearer JWT or API key is valid and discovering
which workspace and permission scopes it grants — call this first when
debugging authentication issues or bootstrapping an SDK integration.

The `auth_kind` field indicates whether the credential is a session token
(`clerk`) or a programmatic key (`api_key`). For API keys, `workspace_id`
and `api_key_id` are always populated; for session tokens, `workspace_id`
reflects the `X-Workspace-Id` header value (if present) and `api_key_id`
is `null`. The `scopes` list is sorted and deduplicated.
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

## dictionary
<details><summary><code>client.dictionary.<a href="src/onepin/dictionary/client.py">list_dictionary_entries</a>(...) -> ApiListResponseDictionaryOut</code></summary>
<dl>
<dd>

#### 📝 Description

<dl>
<dd>

<dl>
<dd>

List dictionary entries for a single locale in the current workspace.

Returns a paginated list of entries for the BCP-47 `language` locale
specified via the `?language=` query parameter (required, e.g. `ko-kr`).
Use `GET /dictionary/search` instead when you need to match by word text
across multiple locales, or `GET /dictionary/languages` to discover which
locales have entries before filtering here.

`audio_url` on entries with `method=recorded` is a short-lived presigned URL
— do not cache it across sessions.
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

**method:** `typing.Optional[typing.List[DictionaryMethod]]` — Filter by one or more entry methods. Repeat to OR: `?method=spelled&method=recorded`. Omit to return all methods.
    
</dd>
</dl>

<dl>
<dd>

**sort:** `typing.Optional[ListDictionaryEntriesApiV1DictionaryGetRequestSort]` — Field to sort by. `uses_count` ranks the most-applied entries first, useful for auditing high-impact corrections.
    
</dd>
</dl>

<dl>
<dd>

**order:** `typing.Optional[ListDictionaryEntriesApiV1DictionaryGetRequestOrder]` — Sort direction.
    
</dd>
</dl>

<dl>
<dd>

**offset:** `typing.Optional[int]` — Zero-based pagination offset.
    
</dd>
</dl>

<dl>
<dd>

**limit:** `typing.Optional[int]` — Page size (max 50).
    
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

Create a pronunciation dictionary entry in the current workspace.

Dictionary entries teach the synthesis pipeline how to pronounce words that
it would otherwise handle incorrectly — brand names, acronyms, technical
terms, proper nouns, and foreign loanwords. Each entry is scoped to a single
BCP-47 locale and is applied during workflow execution when that locale is
the synthesis target.

Three methods are supported via the `method` field:

- `spelled` — provide a phonetic respelling in `pronunciation` (e.g.
  `"Poh-doh-nohs"`). `pronunciation` is required for this method.
- `recorded` — attach a reference audio clip by supplying an `upload_id`
  from a completed `/uploads` staging upload with category `dictionary`.
  The audio is copied to permanent storage on create; the upload slot is
  consumed and cannot be reused for a different entry.
- `ipa` — supply an IPA transcription in `ipa`. `pronunciation` is optional
  as a human-readable gloss alongside the IPA.

Returns 409 if a `(word, language)` pair already exists in the workspace.
Requires `editor` workspace role and the `dictionary:write` scope.
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

**word:** `str` — The surface form of the word or phrase as it appears in a script.
    
</dd>
</dl>

<dl>
<dd>

**method:** `DictionaryMethod` — Pronunciation method: `spelled` (phonetic respelling), `recorded` (reference audio clip), or `ipa` (IPA transcription).
    
</dd>
</dl>

<dl>
<dd>

**language:** `str` — BCP-47 locale this entry applies to (e.g. `ko-kr`). Case-insensitive; stored lowercase.
    
</dd>
</dl>

<dl>
<dd>

**workspace_id:** `typing.Optional[str]` 
    
</dd>
</dl>

<dl>
<dd>

**description:** `typing.Optional[str]` — Optional human-readable note about the entry (e.g. context, source).
    
</dd>
</dl>

<dl>
<dd>

**pronunciation:** `typing.Optional[str]` — Phonetic respelling. Required when `method` is `spelled`.
    
</dd>
</dl>

<dl>
<dd>

**upload_id:** `typing.Optional[str]` — ID of a completed staging upload (category `dictionary`). Required when `method` is `recorded`; consumed on create.
    
</dd>
</dl>

<dl>
<dd>

**ipa:** `typing.Optional[str]` — IPA transcription of the word. Supplied by the caller; automatic generation is a planned enhancement.
    
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

Search dictionary entries by word text across one or more locales.

Performs a case-insensitive substring match on the `word` field. Optionally
narrow to one or more BCP-47 locales by repeating `?language=` (OR logic).
Omitting `language` searches across all locales in the workspace.

Use `GET /dictionary` (locale-scoped list) when you want the full entry list
for a specific locale; use this endpoint when you need to find how a word
is defined across languages or when the user is typing a search query.
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

**search:** `str` — Substring to match against the `word` field (case-insensitive).
    
</dd>
</dl>

<dl>
<dd>

**sort:** `typing.Optional[SearchDictionaryEntriesApiV1DictionarySearchGetRequestSort]` — Field to sort by.
    
</dd>
</dl>

<dl>
<dd>

**order:** `typing.Optional[SearchDictionaryEntriesApiV1DictionarySearchGetRequestOrder]` — Sort direction.
    
</dd>
</dl>

<dl>
<dd>

**offset:** `typing.Optional[int]` — Zero-based pagination offset.
    
</dd>
</dl>

<dl>
<dd>

**limit:** `typing.Optional[int]` — Page size (max 50).
    
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

Return all locales that have at least one dictionary entry, with entry counts.

Results are ordered by entry count descending, then BCP-47 locale code
ascending. Use this endpoint to populate a locale filter dropdown before
calling `GET /dictionary?language=`, rather than hard-coding the supported
locale list in your client.
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

Generate a pronunciation suggestion for a word before saving it as a dictionary entry.

Returns a `pronunciation` string suitable for use as the `pronunciation` field
when creating a `spelled`-method dictionary entry. The suggestion is
deterministic (same word always returns the same result) and is intended as a
starting point for human review, not as a production-ready transcription.

`language` is accepted to maintain a consistent request shape for future
per-locale phonetic rules; it does not affect the current output. `ipa` is
always `null` in this version — automatic IPA generation is a planned
enhancement.
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

**word:** `str` — The word or phrase to generate a pronunciation suggestion for.
    
</dd>
</dl>

<dl>
<dd>

**language:** `str` — BCP-47 locale of the word. Reserved for future per-locale phonetic rules; does not affect current output.
    
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

Update fields on an existing dictionary entry in the current workspace.

Supports partial updates — only the fields included in the request body are
changed; omitted fields retain their current values. Passing `null` for
`word`, `method`, or `language` is rejected with 422, as these fields are
required on the stored entry.

To replace the reference audio on a `recorded`-method entry, supply a new
`upload_id` pointing to a completed staging upload. The previous audio is
orphaned (not deleted from storage) and the new file is copied to permanent
storage atomically.

Returns 409 if the new `(word, language)` combination already exists in the
workspace. Requires `editor` workspace role and the `dictionary:write` scope.
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

**word:** `typing.Optional[str]` — Updated surface form. Omit to leave unchanged.
    
</dd>
</dl>

<dl>
<dd>

**description:** `typing.Optional[str]` — Updated human-readable note. Omit to leave unchanged.
    
</dd>
</dl>

<dl>
<dd>

**pronunciation:** `typing.Optional[str]` — Updated phonetic respelling. Required when changing `method` to `spelled`.
    
</dd>
</dl>

<dl>
<dd>

**upload_id:** `typing.Optional[str]` — New staging upload ID to replace the reference audio. Required when changing `method` to `recorded`.
    
</dd>
</dl>

<dl>
<dd>

**method:** `typing.Optional[DictionaryMethod]` — Updated pronunciation method. Omit to leave unchanged.
    
</dd>
</dl>

<dl>
<dd>

**language:** `typing.Optional[str]` — Updated BCP-47 locale. Omit to leave unchanged.
    
</dd>
</dl>

<dl>
<dd>

**ipa:** `typing.Optional[str]` — Updated IPA transcription. Omit to leave unchanged; supply `null` explicitly to clear.
    
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

Delete a dictionary entry from the current workspace.

The entry is removed from the workspace's dictionary and will no longer
influence synthesis output in subsequent workflow runs. The operation is not
reversible via the API — create a new entry to restore the pronunciation.
Returns an empty `data` object on success. Requires `editor` workspace role
and the `dictionary:write` scope.
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

List all available node types with their input/output port schemas.

Returns the static structural definition for every node type registered in
the catalog — what ports each node exposes, their names, and expected data
shapes — without runtime-variable values such as available languages or the
TTS model catalog. This endpoint requires no `X-Workspace-Id` header and no
authentication, making it suitable for static documentation generation and
canvas layout tooling.

For the full runtime configuration options a user would pick when wiring up
a specific node (available target languages, provider/model options, voice
picker URL), use `GET /api/v2/nodes/{node_type}` instead.
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

Return full node definition and runtime configuration options for a node type.

**Deprecated:** use `GET /api/v2/nodes/{node_type}` instead. This v1 variant
inlines the full TTS model catalog under `options.models_by_provider`, which
creates a large response and couples clients to the catalog structure. The v2
endpoint replaces that inline tree with a `providers` HATEOAS href pointing to
the standalone `/api/v1/providers` catalog, so the model list is fetched lazily
only when needed.

Unlike `GET /nodes` (which returns only static port schemas), this endpoint
returns the runtime values a caller uses to configure a node: supported target
languages derived from deployment settings, the available model catalog, and a
HATEOAS link to the workspace-scoped voice list. Requires `X-Workspace-Id`.
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

<details><summary><code>client.nodes.<a href="src/onepin/nodes/client.py">get_node_detail_v2</a>(...) -> ApiResponseNodeDetailOut</code></summary>
<dl>
<dd>

#### 📝 Description

<dl>
<dd>

<dl>
<dd>

Return full node definition and runtime configuration options for a node type (v2).

Extends `GET /api/v1/nodes/{node_type}` by replacing the large inline model
catalog (`options.models_by_provider`) with a `providers` HATEOAS href pointing
to `GET /api/v1/providers`. Clients follow that link to load the model list and
each model's configuration schema only when the user opens the relevant
configuration panel, rather than receiving it in every node-detail response.

The `voices` HATEOAS href (with its provider, model, and language filter
parameters) is unchanged from v1, so the voice picker does not require a
catalog call. Supported target languages are resolved from deployment settings
at request time. Requires `X-Workspace-Id` and the `catalog:read` scope.
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

client.nodes.get_node_detail_v2(
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

## providers
<details><summary><code>client.providers.<a href="src/onepin/providers/client.py">list_catalog_providers</a>(...) -> ApiListResponseCatalogProviderOut</code></summary>
<dl>
<dd>

#### 📝 Description

<dl>
<dd>

<dl>
<dd>

List all available speech synthesis providers in the catalog.

Returns the full set of speech synthesis providers — each with its display name,
number of available models, and a HATEOAS `models` link to
`GET /providers/{provider}/models`. The response contains only
customer-facing metadata; cost, credentials, and base URLs are never included.

This endpoint is the starting point for building a provider/model/voice
selection flow. The typical traversal is: list providers → follow `models`
link → follow `voices` link for the chosen model. Requires `X-Workspace-Id`
and the `catalog:read` scope.
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

client.providers.list_catalog_providers()

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

<details><summary><code>client.providers.<a href="src/onepin/providers/client.py">get_catalog_provider</a>(...) -> ApiResponseCatalogProviderOut</code></summary>
<dl>
<dd>

#### 📝 Description

<dl>
<dd>

<dl>
<dd>

Get a single speech synthesis provider by its canonical identifier.

Returns the same shape as an item in `GET /providers` — display name, model
count, and a HATEOAS `models` link — but scoped to a single provider. Returns
404 if the provider identifier is not recognized. The canonical identifier is
the lowercase slug returned in the `provider` field of the list response.
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

client.providers.get_catalog_provider(
    provider="provider",
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

**provider:** `str` 
    
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

<details><summary><code>client.providers.<a href="src/onepin/providers/client.py">list_catalog_provider_models</a>(...) -> ApiListResponseCatalogModelOut</code></summary>
<dl>
<dd>

#### 📝 Description

<dl>
<dd>

<dl>
<dd>

List all models available for a given provider.

Returns each model's display name, content type, live `voice_count` (the
number of platform voices catalogued under that model), and a `controls` map
describing the canonical provider-agnostic parameters supported by the model
(e.g. speed, stability). Also includes `config_schema` for back-compat — new
integrations should prefer `controls` as the authoritative parameter
description. Each item includes a HATEOAS `voices` link to the paginated
voice list for that model. Returns 404 if the provider is not recognized.
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

client.providers.list_catalog_provider_models(
    provider="provider",
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

**provider:** `str` 
    
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

<details><summary><code>client.providers.<a href="src/onepin/providers/client.py">list_catalog_provider_model_voices</a>(...) -> ApiCountedListResponseCatalogVoiceOut</code></summary>
<dl>
<dd>

#### 📝 Description

<dl>
<dd>

<dl>
<dd>

List platform voices available for a specific provider and model.

Returns a paginated list of voices from the platform catalog (system
workspace) that declare support for the given `model`. A voice can appear
under multiple models when its `supported_models` list includes more than
one entry; voices with no supported models are excluded from all model
listings.

Each voice includes gender, age, accent, supported locales, and a short-lived
presigned `preview_url` for the audio sample — do not cache these URLs across
sessions. The response `pagination.total` field reflects the total match count
for the provider/model pair.

For the workspace voice picker (which merges platform and workspace-scoped
voices and supports favorite/similarity filtering), use `GET /voices` with
`?provider=` and `?model=` query parameters instead.

Returns 404 if the provider or model is not recognized.
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

client.providers.list_catalog_provider_model_voices(
    provider="provider",
    model="model",
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

**provider:** `str` 
    
</dd>
</dl>

<dl>
<dd>

**model:** `str` 
    
</dd>
</dl>

<dl>
<dd>

**offset:** `typing.Optional[int]` — Zero-based pagination offset.
    
</dd>
</dl>

<dl>
<dd>

**limit:** `typing.Optional[int]` — Page size (max 100).
    
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

<details><summary><code>client.providers.<a href="src/onepin/providers/client.py">get_catalog_provider_model</a>(...) -> ApiResponseCatalogModelOut</code></summary>
<dl>
<dd>

#### 📝 Description

<dl>
<dd>

<dl>
<dd>

Get a single model for a given provider.

Returns the same shape as an item in `GET /providers/{provider}/models`,
including `controls` (canonical parameter map), `config_schema` (for
back-compat), live `voice_count`, and a HATEOAS `voices` link. Returns 404
if the provider or model identifier is not recognized.
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

client.providers.get_catalog_provider_model(
    provider="provider",
    model="model",
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

**provider:** `str` 
    
</dd>
</dl>

<dl>
<dd>

**model:** `str` 
    
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

Browse the public template gallery across all workspaces.

Returns only templates that have an active published snapshot (`is_public=true`,
`published_definition` set, not unpublished). Results come from any workspace —
the gallery is intentionally cross-workspace so callers can discover shared
starting points regardless of their own workspace membership.

Does not require `X-Workspace-Id`, so callers without a workspace (e.g. during
onboarding) can still browse. The response reflects the published snapshot for
each row, not any unpublished draft edits.

Dual-auth: Bearer JWT or API key (scope `templates:read`).
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

**category:** `typing.Optional[typing.List[TemplateCategory]]` — Filter by category. Repeat the parameter for OR logic, e.g. `?category=media&category=creative`.
    
</dd>
</dl>

<dl>
<dd>

**search:** `typing.Optional[str]` — Full-text search over template name and description.
    
</dd>
</dl>

<dl>
<dd>

**sort:** `typing.Optional[ListTemplatesRequestSort]` — Sort order: `recent` (last published), `popular` (most cloned), or `name` (alphabetical).
    
</dd>
</dl>

<dl>
<dd>

**offset:** `typing.Optional[int]` — Zero-based offset for page navigation.
    
</dd>
</dl>

<dl>
<dd>

**limit:** `typing.Optional[int]` — Maximum number of templates to return (1–100).
    
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

Create a reusable workflow template in the current workspace.

Templates are workspace-private on creation (`is_public=false`, `is_starter=false`).
The full `WorkflowDefinition` (graph + execution config) is validated at write
time — structural errors (duplicate node/edge IDs, port mismatches, etc.) surface
here rather than when a caller later clones the template into a workflow.

Use this to capture a workflow configuration you intend to reuse or share. To
make a template available in the public gallery, an admin must mark it public
via the admin API. To create a runnable workflow from an existing template,
use `POST /templates/{id}/clone` instead.

Requires workspace `editor` role or higher.
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

**name:** `str` — Display name for the template (1–200 characters, not blank).
    
</dd>
</dl>

<dl>
<dd>

**workspace_id:** `typing.Optional[str]` 
    
</dd>
</dl>

<dl>
<dd>

**description:** `typing.Optional[str]` — Optional human-readable description shown in the gallery (max 2,000 characters).
    
</dd>
</dl>

<dl>
<dd>

**category:** `typing.Optional[TemplateCategory]` — Optional category tag used for gallery filtering.
    
</dd>
</dl>

<dl>
<dd>

**definition:** `typing.Optional[WorkflowDefinitionInput]` — Full workflow definition (graph + execution config). Validated at write time — structural errors are rejected with 422.
    
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

Fetch a single template by ID.

Returns the template if it is visible to the caller: templates owned by the
caller's workspace are returned with the live draft definition; public/starter
templates from other workspaces are returned with the published snapshot.

Returns 404 for templates that exist but are not visible to the caller (not
owned, not public, not a starter) — same response as for a missing ID.

Dual-auth: Bearer JWT or API key (scope `templates:read`).
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

**template_id:** `str` — Case-sensitive 8-character base62 template identifier.
    
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

Delete a template owned by the caller's workspace.

The delete is a soft delete — the record is hidden from the gallery and
all visibility checks immediately, but is not physically removed. Any
workflows previously cloned from this template are unaffected; clone
creates an independent copy of the definition at clone time.

Restrictions:
- Only the owning workspace may delete its templates (403 otherwise).
- Platform starter templates (`is_starter=true`) cannot be deleted (403).

Requires workspace `editor` role or higher.
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

**template_id:** `str` — Case-sensitive 8-character base62 template identifier.
    
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

Update a template owned by the caller's workspace.

All fields are optional (omit to keep the stored value). When `definition`
is supplied it is a full replace — send the complete graph, not a partial
diff. Structural validation runs on write, same as `POST /templates`.

Restrictions:
- Only the owning workspace may update its templates (403 otherwise).
- Platform starter templates (`is_starter=true`) are read-only via this
  endpoint regardless of workspace ownership (403).
- Updates apply only to the draft/live definition; the published gallery
  snapshot is not updated until an admin republishes.

Requires workspace `editor` role or higher.
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

**template_id:** `str` — Case-sensitive 8-character base62 template identifier.
    
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

Estimate the credit cost of running a workflow built from this template.

Returns a per-unit pricing guide expressed in credits per
`unit_chars` input characters (default 1,000). Because the template does not
contain the caller's actual script, the estimate uses a synthetic fixed-length
input to compute a reproducible per-unit rate. Multiply by your expected
character count to project total cost.

The response distinguishes variable costs (scale with script length, e.g.
synthesis) from fixed costs (apply once per run regardless of length). A
node-level breakdown is included so callers can see which processing steps
drive the cost.

Results are cached against the template definition and current pricing rates.
`cache_status` indicates whether this response was served from cache (`hit`),
computed fresh (`miss`), or recomputed because the definition or rates changed
(`stale`).

Visibility rules match `GET /templates/{id}` — own-workspace templates use the
draft definition; cross-workspace templates use the published snapshot.

Dual-auth: Bearer JWT or API key (scope `templates:read`).
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

**template_id:** `str` — Case-sensitive 8-character base62 template identifier.
    
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

Create a runnable workflow in the caller's workspace from a template.

This is the primary way to use a template: it produces a new `Workflow`
owned by the caller's workspace, ready to accept scripts and run jobs.

Use `body.name` to set the workflow name; omit it (or send blank/whitespace)
to get the default `"{template name} (Copy)"`.

Cross-workspace clones (gallery/starter templates) copy the published
snapshot so unpublished draft edits made by the template owner never leak to
other workspaces. Same-workspace clones copy the live draft definition.

Use `GET /templates/{id}/estimate` first to preview credit costs before
committing to a clone and run. Use `POST /workflows/{id}/duplicate` to copy
an existing workflow rather than starting from a template.

Requires workspace `editor` role or higher.
Dual-auth: Bearer JWT or API key (scope `workflows:write`).
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

**template_id:** `str` — Case-sensitive 8-character base62 template identifier.
    
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

Add a template to the current user's favorites.

Favorites are per-user, not per-workspace — the same favorite list is
visible regardless of which workspace the caller is currently acting in.
Any template visible to the caller (own workspace, public, or starter) can
be favorited.

Returns 404 when the template does not exist or is not visible to the caller.
Calling this endpoint on an already-favorited template is idempotent (returns
200 with the template). Use `DELETE /templates/{id}/favorite` to remove.
Does not require `X-Workspace-Id`.
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

**template_id:** `str` — Case-sensitive 8-character base62 template identifier.
    
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

Remove a template from the current user's favorites.

Idempotent and non-enumerating: returns an empty success response whether
or not the favorite or the template exists. Does not require `X-Workspace-Id`.
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

**template_id:** `str` — Case-sensitive 8-character base62 template identifier.
    
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

`language` matches a voice when any of its declared locales matches any
requested value. A voice with no declared locales matches NO `language`
filter — it must positively declare a locale to surface under it. This holds
for platform and user-uploaded voices alike: an unclassified platform voice
(catalog gap) is not treated as general-use, and a user-uploaded/cloned voice
with no locale stays "language unknown" pending clone-flow detection.

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

**offset:** `typing.Optional[int]` — Number of results to skip for pagination.
    
</dd>
</dl>

<dl>
<dd>

**limit:** `typing.Optional[int]` — Maximum number of results to return (1–100).
    
</dd>
</dl>

<dl>
<dd>

**favorites_only:** `typing.Optional[bool]` — When true, return only voices in the workspace's favorites list.
    
</dd>
</dl>

<dl>
<dd>

**source:** `typing.Optional[typing.List[ListVoicesRequestSourceItem]]` — Repeat for OR across scopes: `platform` for system-provided voices, `workspace` for workspace-owned voices.
    
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

**search:** `typing.Optional[str]` — Searches name, tags, and the voice's summary-derived descriptor text (closely tracks the served description; summary beyond 200 chars is not searched).
    
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

**provider:** `typing.Optional[typing.List[str]]` — Repeat for OR, e.g. ?provider=elevenlabs&provider=rime
    
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

<details><summary><code>client.voices.<a href="src/onepin/voices/client.py">get_voice_facets</a>(...) -> ApiResponseVoiceFacetsOut</code></summary>
<dl>
<dd>

#### 📝 Description

<dl>
<dd>

<dl>
<dd>

Filter-bar options (chips) for the voice browser, one list per dimension.

Returns `providers`, `models`, `languages` (data-driven) plus `genders`,
`ages`, `categories`, `accents` (fixed enums) as `VoiceFacetItem[]` so the FE
builds the whole filter bar — with per-chip count badges — in a single request
instead of hardcoding option lists (mirrors `GET /dictionary/languages`). Each
item is `{value, label, count}`: `value` is passed straight back to
`GET /voices`; `label` is the display name for providers/models and `null`
elsewhere (the FE owns language + enum labels); `count` is the number of
matching voices. A language surfaces as one chip keyed by its canonical
allowlist locale: every declared locale is folded onto the locale the
`GET /voices` filter would match it against (bare `ko` and regioned `ko-kr`
both count under `ko-kr`), so variants never split into duplicate chips for
the identical filter. Model counts include only voices that explicitly declare
the model. Language counts include voices that declare the exact regional locale
plus voices that declare its bare family (`en` contributes to every supported
`en-*` locale). A voice with no declared `supported_models` is "general use" —
`GET /voices` matches it against every model filter but no `models` chip counts
it, so a model chip's count can be lower than the `GET /voices?model=` result.
Languages have no such gap: no-locale voices are excluded from both the language
chips and `GET /voices?language=`, so language chip counts match the row counts.

Accepts the SAME filters as `GET /voices` (tab scope `source`/`favorites_only`,
plus `provider`/`model`/`language`/`gender`/`age`/`category`/`accent`/`search`).
`count` is context-aware (faceted search): each dimension's counts apply every
OTHER active filter but exclude that dimension's own selection — e.g. with
`provider=elevenlabs` the language counts are scoped to ElevenLabs, while the
provider chips still show every provider so the caller can switch.

Count-0 policy: data-driven dimensions omit count-0 values (only present ones,
each a valid `GET /voices` filter — providers/models restricted to the enabled
catalog, languages to the supported-locale allowlist, so a chip never 422s).
Enum dimensions always return the full enum in natural order, count-0 included,
for the FE to grey out.
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

client.voices.get_voice_facets()

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

**favorites_only:** `typing.Optional[bool]` — Favorites tab scope
    
</dd>
</dl>

<dl>
<dd>

**source:** `typing.Optional[typing.List[GetVoiceFacetsApiV1VoicesFacetsGetRequestSourceItem]]` — Tab scope — repeat for OR, same values as GET /voices (e.g. platform, workspace)
    
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

**provider:** `typing.Optional[typing.List[str]]` — Repeat for OR, e.g. ?provider=elevenlabs&provider=rime
    
</dd>
</dl>

<dl>
<dd>

**model:** `typing.Optional[typing.List[str]]` — Repeat for OR. Filters platform voices by TTS model, e.g. ?model=arcana&model=sonic-2
    
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

<details><summary><code>client.voices.<a href="src/onepin/voices/client.py">get</a>(...) -> ApiResponseVoiceOut</code></summary>
<dl>
<dd>

#### 📝 Description

<dl>
<dd>

<dl>
<dd>

Fetch a single voice by its ID.

Returns both platform (system-wide) voices and voices that belong to the
caller's workspace. Returns 404 when the voice does not exist or is not
accessible to the caller's workspace. The `sample_url` field is a
time-limited presigned URL valid for 1 hour; regenerate it by calling this
endpoint again rather than caching it long-term.
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

Return voices acoustically similar to a reference voice.

Results are ranked by semantic similarity score (descending) and include the
reference voice's workspace voices and all platform voices. Each result
includes a `similarity_score` between 0 and 1. Optionally filter by one or
more `language` BCP-47 codes (repeat the parameter for OR semantics); up to
16 language values are accepted. Returns 503 when the reference voice has no
embedding yet — retry after the indicated `Retry-After` interval. Prefer this
endpoint over `GET /voices` with manual filtering when building a
"voices like this" recommendation UI.
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

**limit:** `typing.Optional[int]` — Number of similar voices to return (1–50).
    
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

Add a voice to the current workspace's favorites.

Favorites are workspace-scoped, not per-user: all members of the workspace
see the same favorited set. Idempotent — favoriting a voice that is already
favorited succeeds without error. Returns the voice with `is_favorite=true`.
Requires the caller to have at least editor role in the workspace.
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

Remove a voice from the current workspace's favorites.

Idempotent — removing a voice that is not currently favorited succeeds
without error. Requires the caller to have at least editor role in the
workspace.
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

Return workspace-level settings for the specified workspace.

Currently exposes `default_language` (the locale used as the default for
new workflow nodes) and `theme` (the workspace's display color theme).
Settings are workspace-scoped: all members of the workspace share the
same values. Per-user preferences (e.g. personal dark mode) are outside
the scope of this endpoint.

If settings have not yet been explicitly configured for the workspace,
defaults are returned (and persisted) on first access.
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

Returns a unified list combining confirmed members (status `active`) and
outstanding invites that have not yet been accepted or revoked (status
`invited`). Pending invites appear with `user_id: null` and only the
`email` and `role` fields populated.

The list is sorted: the requesting user appears first, then admins by
join date, then other members by join date. No pagination — the full
roster is returned in a single response.

Roles:
- `admin`: can manage members, invites, workspace settings, and all content.
- `editor`: can create, edit, and run workflows; cannot manage members.
- `viewer`: read-only access to workspace content and run history.
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

Invite a user to the workspace by email. Admin only.

Creates a pending invite and sends an invitation email to the specified
address. The invitee does not need to have an existing account — they can
sign up after receiving the invite. The invite includes a role
(`admin`, `editor`, or `viewer`) that the invitee will receive upon
accepting.

Invites expire after 14 days. Only one pending invite per email address
per workspace is allowed at a time; re-inviting the same address while a
pending invite exists returns 409. Inviting an address that already
belongs to an active member also returns 409.

The invitee's role can be updated before acceptance via
`PATCH /workspaces/{ws_id}/invites/{invite_id}`, or the invite can be
cancelled via `DELETE /workspaces/{ws_id}/invites/{invite_id}`.
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

**email:** `str` — Email address to invite. Normalized to lowercase. Returns 409 if this address is already an active member or has a pending invite.
    
</dd>
</dl>

<dl>
<dd>

**role:** `WorkspaceRole` — Role to grant when the invite is accepted: `admin`, `editor`, or `viewer`.
    
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

Remove an active member from the workspace. Admin only.

The removed member immediately loses access to all workspace resources.
They receive an email notification informing them they have been removed.

Two protections prevent accidental lockouts:
- The workspace owner cannot be removed.
- The last remaining admin cannot be removed (returns 409).

Removing a member does not affect their account or other workspaces. To
block an invited but not-yet-accepted user instead, revoke the invite via
`DELETE /workspaces/{ws_id}/invites/{invite_id}`.
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

Change a workspace member's role. Admin only.

Updates the role of an active member to `admin`, `editor`, or `viewer`.
The operation is idempotent — setting a member to their current role
succeeds silently (no error, no duplicate email notification).

Two protections prevent accidental lockouts:
- The workspace owner's role cannot be changed.
- The last remaining admin cannot be demoted (returns 409).

When the role actually changes, the affected member receives an email
notification describing their new permissions.
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

Cancel a pending invite so the invitee can no longer accept it. Admin only.

The invite token is invalidated immediately. If the invitee attempts to
accept after revocation, they receive a 410 Gone. The invite is removed
from the pending list returned by `GET /workspaces/{ws_id}/members`.

Revoking an invite that is already accepted, revoked, or expired returns
404. To remove an already-accepted member, use
`DELETE /workspaces/{ws_id}/members/{member_id}`.
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

Change the role on a pending (not yet accepted) invite. Admin only.

Updates the role the invitee will receive when they accept. Only pending
invites can be updated — attempting to update an accepted, revoked, or
expired invite returns 409. The invitee is not notified of the role
change; the updated role takes effect when they accept.
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

Accept a workspace invite using the token from the invitation email.

The `token` path parameter comes from the invitation link sent to the
invitee's email. The caller must be authenticated and their verified email
address must match the address the invite was sent to (403 if it does not).

On success the caller is added to the workspace with the role specified in
the invite, and `workspace_id` is returned so the caller can immediately
begin using that workspace. If the caller is already a member of the
workspace (e.g. accepted via a different device), the accept is idempotent
and returns the same `workspace_id`.

Error cases (all return 410 Gone):
- Invite already accepted.
- Invite was revoked by an admin.
- Invite has expired (14-day TTL from creation).
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

List all workspaces the current user is a member of.

Returns workspaces where the caller has any role (admin, editor, or
viewer), including workspaces they own and workspaces they joined via
invite. Results are paginated; omits soft-deleted workspaces and the
internal system workspace.
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

Workspaces are the top-level container for all resources (workflows,
voices, dictionary entries, members). Every resource is scoped to exactly
one workspace via the `X-Workspace-Id` header on subsequent requests.

The authenticated user becomes the workspace owner and is automatically
added as an `admin` member. An optional `slug` (1–50 characters,
lowercase kebab-case) can be supplied for a human-readable workspace
identifier; if omitted, one is auto-generated from `name`. Returns 409
if the slug is already taken, 422 if the slug format is invalid or uses
a reserved word.

The number of workspaces a user may own is plan-gated. Attempting to
exceed the limit returns 402.
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

**name:** `str` — Human-readable workspace name (1–200 characters, non-blank).
    
</dd>
</dl>

<dl>
<dd>

**slug:** `typing.Optional[str]` — Optional URL-safe identifier (lowercase kebab-case, 1–50 characters). Auto-generated from `name` if omitted. Returns 409 if taken, 422 if invalid or reserved.
    
</dd>
</dl>

<dl>
<dd>

**color_idx:** `typing.Optional[int]` — Index into the workspace color palette (0–6).
    
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

<details><summary><code>client.workspaces.<a href="src/onepin/workspaces/client.py">slug_available</a>(...) -> ApiResponseSlugAvailabilityOut</code></summary>
<dl>
<dd>

#### 📝 Description

<dl>
<dd>

<dl>
<dd>

Check whether a slug is available for the current workspace. Admin only.

Returns `{ available: true }` if the slug is valid, not reserved, and
not already claimed by another workspace. When unavailable, `reason`
indicates why: `invalid` (format/length), `reserved` (blocked word), or
`taken` (already in use globally). The workspace's own current slug is
self-excluded, so an admin can safely check their existing slug without
receiving `taken`.

This is an advisory point-in-time check — a concurrent `POST /workspaces`
or `PATCH /workspaces/{id}` from another session can claim the slug
between this response and the caller's write. Always handle 409
`WORKSPACE_SLUG_TAKEN` on `create_workspace` and `update_workspace`.

Requires the `X-Workspace-Id` header (the workspace being renamed) and
admin role in that workspace. Missing/invalid header returns 400; not a
member returns 404; not admin returns 403.
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

client.workspaces.slug_available(
    slug="slug",
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

**slug:** `str` — Candidate slug; normalized (strip().lower()) before checks.
    
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

<details><summary><code>client.workspaces.<a href="src/onepin/workspaces/client.py">get_workspace</a>(...) -> ApiResponseWorkspaceOut</code></summary>
<dl>
<dd>

#### 📝 Description

<dl>
<dd>

<dl>
<dd>

Fetch a single workspace by ID.

Returns the workspace if the current user is an active member (any role).
Returns 404 if the workspace does not exist, has been deleted, or the
caller is not a member — the two cases are intentionally indistinguishable
to prevent workspace enumeration.
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

Delete a workspace and all of its resources. Owner only.

Soft-deletes the workspace and cascades to all owned resources (workflows,
voices, dictionary entries, members, etc.). The workspace and its contents
become inaccessible via the API immediately. Data is retained for the GDPR
retention period before permanent purge.

Only the workspace owner (the user who created it) can delete it; admin
members who are not the owner receive 404. Returns 404 if the workspace
does not exist or the caller is not the owner.
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

Update a workspace's name, color palette index, and/or slug. Admin only.

All fields are optional — supply only the fields you want to change.
`slug` follows the same validation rules as on create (lowercase
kebab-case, 1–50 characters, no reserved words). Returns 409 if the new
slug is already claimed by another workspace, 422 if the slug format is
invalid or reserved. Re-setting the workspace's current slug to itself
never returns 409.

Only workspace admins may call this endpoint; other members receive 404
(same as not-found, to avoid leaking membership details to non-members).
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

**name:** `typing.Optional[str]` — New workspace name. Omit to leave unchanged.
    
</dd>
</dl>

<dl>
<dd>

**slug:** `typing.Optional[str]` — New slug (lowercase kebab-case, 1–50 characters). Omit to leave unchanged. Returns 409 if taken, 422 if invalid or reserved.
    
</dd>
</dl>

<dl>
<dd>

**color_idx:** `typing.Optional[int]` — New color palette index (0–6). Omit to leave unchanged.
    
</dd>
</dl>

<dl>
<dd>

**routing_price_sensitivity:** `typing.Optional[float]` — New voice-selection price/quality balance (0.0 = pure quality, 1.0 = pure price, 0.5 = balanced). Omit to leave unchanged.
    
</dd>
</dl>

<dl>
<dd>

**routing_llm_fit:** `typing.Optional[bool]` — New setting for whether automatic voice selection also weighs content fit. Omit to leave unchanged.
    
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

Request a presigned URL to upload a file to object storage (step 1 of 2).

The two-step upload flow:
1. `POST /uploads` — register the file and receive a short-lived `upload_url`.
   PUT your file bytes directly to that URL (do not send them to this API).
2. `POST /uploads/{id}` — confirm the upload completed and bind the file to a
   resource (e.g. a workflow). The file is moved to its final location and the
   upload record transitions from `pending` to `uploaded`.

`category` controls which file formats are accepted:
- `script` — text-based formats (txt, srt, csv, json, xliff, docx)
- `dictionary` — audio formats (mp3, wav, m4a, ogg, webm)

The presigned URL expires within a short window (see `upload_url` TTL in the
response). If the URL expires before the PUT completes, discard this upload
record and start over with a fresh `POST /uploads` call.

`X-Workspace-Id` is optional but recommended for workspace-scoped storage
quota tracking. API keys with a bound workspace attach automatically.

Dual-auth: Bearer JWT or API key (scope `uploads:write`).
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

**filename:** `str` — Original filename including extension (e.g. `script.txt`). Must include a file extension.
    
</dd>
</dl>

<dl>
<dd>

**category:** `UploadRequestCategory` — File category. Determines which formats are accepted: `script` for text formats (txt, srt, csv, json, xliff, docx); `dictionary` for audio formats (mp3, wav, m4a, ogg, webm).
    
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

Confirm a completed upload and bind it to a resource (step 2 of 2).

Call this after successfully PUTting your file to the presigned URL returned
by `POST /uploads`. Provide `context_type` and `context_id` to associate the
file with an existing resource (currently `workflow` is the supported context
type). The file is moved to its final location and `status` transitions from
`pending` to `uploaded`.

This endpoint is idempotent: if the upload was already confirmed, the current
state is returned without re-processing.

Storage quota is checked against the workspace at confirm time. If confirming
would exceed the workspace storage limit, a 402 is returned and the file
remains in its staging location (the upload record stays `pending` so you can
delete the staging file and try a smaller file).

Binding to a workspace-scoped resource requires the caller to be a member of
that workspace. Workspace is inferred from the resource when `X-Workspace-Id`
is omitted.

Dual-auth: Bearer JWT or API key (scope `uploads:write`).
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

**context_type:** `UploadConfirmRequestContextType` — Type of resource this upload is being attached to: `workflow`, `playground`, or `assistant_session`.
    
</dd>
</dl>

<dl>
<dd>

**context_id:** `str` — ID of the resource to attach this upload to. Must be an existing resource of the given `context_type` that the caller has access to.
    
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

Delete an upload and its associated file.

Permanently removes the upload record and schedules the stored file for
deletion. The record is removed first; the file is cleaned up asynchronously
after the response so storage removal only happens after a successful commit.

If the upload was previously confirmed against a workspace-scoped resource,
the consumed storage bytes are released back to the workspace quota, keeping
the workspace storage counter accurate.

Callers can delete uploads in any state (`pending` or `uploaded`). Deleting
a `pending` upload (e.g. after an expired presigned URL) is the correct way
to clean up an abandoned upload attempt.

Dual-auth: Bearer JWT or API key (scope `uploads:write`).
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

Return aggregated usage totals and activity chart data for the workspace.

Combines credit consumption, character and line counts, and workflow run
statistics for the requested rolling window (`range`) with a chart-ready
activity series (`activity`) bucketed by `activity_view`.

The `credits.used` field reflects the authenticated user's own billing-period
consumption; all other aggregate fields (characters, lines, runs, daily
buckets, activity buckets) are workspace-scoped across all members.

Date boundaries are computed in the supplied `timezone` (IANA, e.g.
`America/New_York`) so "today" and "this week" align with the caller's local
calendar. Defaults to UTC.

Use `GET /usage/by-language` for a language-level breakdown, or
`GET /usage/activity` for the event-by-event feed.

Dual-auth: Bearer JWT or API key (scope `workspace:read`).
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

Return workspace audio generation usage broken down by language.

Each row represents one locale with its share of total credit and character
consumption. `share` is a 0..1 fraction of workspace-wide usage for the
period; multiply by 100 for a percentage.

Period selection: supply `activity_view` to align the language rows with
the same period shown on the Usage dashboard chart (daily = last 7 local
days, weekly = last 12 Monday-start weeks, monthly = last 12 months). When
`activity_view` is provided, `range` is ignored and `range` in the response
is `null`. Omit `activity_view` to use the rolling `range` window instead.

Date boundaries are computed in the supplied `timezone` (IANA). Defaults to UTC.

Dual-auth: Bearer JWT or API key (scope `workspace:read`).
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

Return the workspace activity feed as a cursor-paginated event list.

Each item represents a discrete workspace event (workflow run, voice generated,
template applied, member invited, API key created, settings changed). Events are
ordered newest-first within the requested rolling window.

Filtering:
- `type` narrows to a single action kind (e.g. `workflow_run`).
- `user_id` restricts to events triggered by a specific workspace member;
  returns 404 if the user is not a member of this workspace.
- Both filters can be combined.

Pagination: pass the `cursor` value from a previous response to retrieve the
next page. An absent or null `cursor` in the response means no further pages
exist. Page size is controlled by `limit` (1–100, default 20).

Date boundaries are computed in the supplied `timezone` (IANA). Defaults to UTC.

Dual-auth: Bearer JWT or API key (scope `workspace:read`).
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

## users
<details><summary><code>client.users.<a href="src/onepin/users/client.py">get_my_credits</a>() -> ApiResponseBalanceResponse</code></summary>
<dl>
<dd>

#### 📝 Description

<dl>
<dd>

<dl>
<dd>

Return the caller's current credit balance and billing period details.

`balance` is the authoritative gate value: use it to decide whether to
attempt a workflow run. `remaining` is a display convenience derived from
settled ledger entries and may temporarily exceed `balance` while a workflow
run holds an open reserve. `used` reflects credits consumed in the current
billing period. `plan_grant` is the total monthly credit allowance for the
caller's plan, enabling a "X / Y used" display. `period_start` is the current
credit anchor and `period_end` is the next EXPECTED credit-reset boundary
(`period_start` + 1 month), or null when no reset is promised — Free/one-time,
unanchored, a canceling/ended entitlement, or a monthly renewal whose boundary
passed without confirmed payment. `period_end` is the expected boundary, not a
guaranteed grant time: monthly credits stay gated on successful Stripe payment.
For an annual subscriber this GET may perform idempotent maintenance, granting
any due intermediate monthly credits before returning; retries remain safe.
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

Return the plan limits that govern the caller's current tier.

Includes numeric quotas (`monthly_credits`, `concurrent_runs_per_user`,
`storage_bytes_per_workspace`, `workspaces_per_owner`) and feature flags
(`byok_enabled`, `auto_fix_enabled`). Use this endpoint to gate feature
access in your application rather than hardcoding tier names, which may
change.
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

<details><summary><code>client.users.<a href="src/onepin/users/client.py">get_current_notification_preferences</a>() -> ApiResponseEmailNotificationPreferencesOut</code></summary>
<dl>
<dd>

#### 📝 Description

<dl>
<dd>

<dl>
<dd>

Return the caller's current email notification settings.

Each boolean field corresponds to a notification category. `true` means the
caller will receive that email; `false` means they have opted out. Use
`PATCH /me/notification-preferences` to change individual preferences.
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

Partially update the caller's email notification preferences.

Send only the fields you want to change; omitted fields are left unchanged.
All provided fields must be boolean — explicit `null` values are rejected
with a 422. Returns the full updated preference object.
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

**completed_generation_email:** `typing.Optional[bool]` — Set to true to enable or false to disable completion emails. Omit to leave unchanged.
    
</dd>
</dl>

<dl>
<dd>

**failed_generation_email:** `typing.Optional[bool]` — Set to true to enable or false to disable failure emails. Omit to leave unchanged.
    
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

List workflow templates created by the caller in the current workspace.

Returns only templates owned by the caller; templates shared by other
workspace members or platform starter templates are not included — use
`GET /api/v1/templates` for the full gallery. Supports offset-based
pagination via `offset` / `limit`. Combine `category`, `search`, and
`favorites_only` to narrow results; multiple `category` values are OR'd.
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

**search:** `typing.Optional[str]` — Full-text search against template name and description.
    
</dd>
</dl>

<dl>
<dd>

**sort:** `typing.Optional[ListMyTemplatesApiV1UsersMeTemplatesGetRequestSort]` — Sort order: `recent` (last updated), `name` (A–Z), or `uses` (most used).
    
</dd>
</dl>

<dl>
<dd>

**offset:** `typing.Optional[int]` — Number of results to skip for pagination.
    
</dd>
</dl>

<dl>
<dd>

**limit:** `typing.Optional[int]` — Maximum number of results to return (1–100).
    
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

Returns a counted, paginated list of workflows scoped to the `X-Workspace-Id`
header. Each item includes aggregate stats (`runs_count`, `last_run_at`,
`last_run_status`, `run_status_counts`) computed over all runs for that
workflow. `run_status_counts` is a per-raw-`RunStatus` map whose values sum to
`runs_count` and are NOT affected by the `status` filter below, so a collapsed
row can render an accurate per-tab total without a separate runs query.

**Status filter:** `status` narrows by the UI-derived state of the workflow's
most recent run. `completed` matches only workflows whose latest run succeeded
(completed-only), and `failed` matches only workflows whose latest run failed —
the two buckets are disjoint. A workflow whose latest run was `cancelled` matches
neither bucket and surfaces only in the unfiltered list. `running` matches active
(running or paused) workflows. `draft` matches workflows with no runs yet.
`paused` is accepted but currently returns no results.

**Multi-sort:** `sort` and `order` are parallel query lists.
`?sort=runs_count&sort=name&order=desc&order=asc` orders primarily by
`runs_count DESC`, then by `name ASC`. When `order` has fewer entries than
`sort`, missing positions use per-field defaults (`name=asc`,
`updated_at=desc`, `runs_count=desc`). Omitting `sort` defaults to
`updated_at DESC`. A stable `id ASC` tiebreaker is always appended so
offset/limit pagination is consistent when sort keys tie.

**Date range:** `last_run_after` / `last_run_before` filter by the time of
the most recent run. Both must be ISO 8601 with a UTC offset; a naive
datetime returns 422. An inverted range (`after > before`) also returns 422.

**Failure history:** `has_failed_run` is orthogonal to `status`. `status`
keys off the latest run only; `has_failed_run=true` matches workflows with a
`failed` run *anywhere* in their history, so a workflow whose latest run
completed still matches if an earlier run failed. It composes with the other
filters (AND). `cancelled` runs do not count as failures.

`pagination.total` reflects the filtered count for the current query.
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

**status:** `typing.Optional[WorkflowListStatus]` — UI workflow status filter. `completed` matches workflows whose latest run succeeded (completed-only); `failed` matches failed-only — the two are disjoint. A workflow whose latest run was cancelled matches neither and appears only in the unfiltered list. `paused` is accepted for forward compatibility and currently returns no rows.
    
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

**last_run_after:** `typing.Optional[datetime.datetime]` — Filter workflows whose last_run_at is at or after this ISO datetime (ISO 8601 with UTC offset required).
    
</dd>
</dl>

<dl>
<dd>

**last_run_before:** `typing.Optional[datetime.datetime]` — Filter workflows whose last_run_at is at or before this ISO datetime (ISO 8601 with UTC offset required).
    
</dd>
</dl>

<dl>
<dd>

**has_failed_run:** `typing.Optional[bool]` — Filter by failure history — ORTHOGONAL to `status` (which is latest-run based). `true` returns only workflows with at least one run that ended in `failed` state anywhere in their history; a workflow whose latest run succeeded still matches if an earlier run failed. `false` returns only workflows that have never had a failed run. Composes (ANDs) with `status`/`search`/date filters. `cancelled` runs are not treated as failures.
    
</dd>
</dl>

<dl>
<dd>

**offset:** `typing.Optional[int]` — Zero-based pagination offset.
    
</dd>
</dl>

<dl>
<dd>

**limit:** `typing.Optional[int]` — Maximum items to return (1–100).
    
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

Create a new workflow in the current workspace.

Validates the workflow `definition` (graph structure, node types, edge
connectivity) before persisting. Returns 422 with structured details if
the definition fails validation. Requires at least `editor` role in the
workspace; viewers cannot create workflows.

The `definition` contains a `graph` (nodes and edges) and an `execution`
block (ordered step list and execution params). Omitting `definition`
creates a workflow with an empty graph that can be edited later.
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

**name:** `str` — Human-readable workflow name (1–200 characters, non-blank).
    
</dd>
</dl>

<dl>
<dd>

**workspace_id:** `typing.Optional[str]` 
    
</dd>
</dl>

<dl>
<dd>

**description:** `typing.Optional[str]` — Optional description shown in the workflow list (max 5000 characters).
    
</dd>
</dl>

<dl>
<dd>

**definition:** `typing.Optional[WorkflowDefinitionInput]` — Graph and execution config. Omit to create an empty workflow.
    
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

<details><summary><code>client.workflows.<a href="src/onepin/workflows/client.py">check_workflow_name_availability</a>(...) -> ApiResponseWorkflowNameAvailabilityOut</code></summary>
<dl>
<dd>

#### 📝 Description

<dl>
<dd>

<dl>
<dd>

Check whether a workflow name is free within the current workspace.

Workflow names are unique per workspace among live (non-deleted) workflows,
so this lets a client validate a name before create or rename. The `name` is
trimmed and validated with the same policy as create — an invalid name
returns 422. The check is case-sensitive and ignores soft-deleted workflows,
mirroring the underlying uniqueness constraint. Pass `exclude_id` when
renaming so the workflow's current name is not reported as taken by itself.
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

client.workflows.check_workflow_name_availability(
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

**name:** `str` — Workflow name to check (trimmed before comparison).
    
</dd>
</dl>

<dl>
<dd>

**exclude_id:** `typing.Optional[str]` — Workflow to exclude from the check — its own name then reads as available. Pass the workflow's id when validating a rename.
    
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

<details><summary><code>client.workflows.<a href="src/onepin/workflows/client.py">get</a>(...) -> ApiResponseWorkflowOut</code></summary>
<dl>
<dd>

#### 📝 Description

<dl>
<dd>

<dl>
<dd>

Fetch a single workflow by ID.

Returns the full workflow including its `definition` (graph nodes/edges and
execution config), aggregate run stats, and the latest run status. The
`definition` is returned with any backwards-compatible config migrations
applied, so node configs always reflect the current schema even if the
workflow was saved with an older version.

Use `GET /workflows` to list multiple workflows without fetching their
full definitions.
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

Replace a workflow's name, description, and definition (full update).

All fields in the request body are required. The `definition` is
validated before persisting; an invalid graph returns 422. Existing runs
are not affected — each run captures a `definition_snapshot` at start
time. Requires at least `editor` role. Use `PATCH` to update only
specific fields without supplying the full definition.
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

**name:** `str` — Human-readable workflow name (1–200 characters, non-blank).
    
</dd>
</dl>

<dl>
<dd>

**definition:** `WorkflowDefinitionInput` — Full replacement graph and execution config. Must be valid.
    
</dd>
</dl>

<dl>
<dd>

**workspace_id:** `typing.Optional[str]` 
    
</dd>
</dl>

<dl>
<dd>

**description:** `typing.Optional[str]` — Optional description (max 5000 characters). Pass null to clear.
    
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

Delete a workflow and hide it from all list and get endpoints.

The workflow is soft-deleted: its data (including runs and their outputs)
is retained for audit and GDPR-purge purposes but is no longer accessible
via the API. Subsequent `GET`, `PUT`, `PATCH`, or run requests on the
same ID return 404. Requires at least `editor` role.
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

Partially update a workflow — only supplied fields are changed.

Any combination of `name`, `description`, and `definition` may be
included; omitted fields are left unchanged. At least one field must be
present (empty body returns 422). If `definition` is provided it is fully
validated; an invalid graph returns 422. Requires at least `editor` role.

Use `PUT` when replacing the full workflow definition in one operation.
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

**name:** `typing.Optional[str]` — New workflow name (1–200 characters). Omit to leave unchanged.
    
</dd>
</dl>

<dl>
<dd>

**description:** `typing.Optional[str]` — New description (max 5000 characters). Omit to leave unchanged; pass null to clear.
    
</dd>
</dl>

<dl>
<dd>

**definition:** `typing.Optional[WorkflowDefinitionInput]` — Replacement graph and execution config. Omit to leave unchanged; must be valid if supplied.
    
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

Returns only uploads that have been confirmed (fully transferred and
committed to the workflow), plus confirmed uploads the workflow definition's
Script Input nodes reference by id (e.g. a file attached in the assistant
chat, which stays bound to its assistant session). In-progress or abandoned
uploads are excluded. Each item includes a short-lived download URL for the
uploaded file.
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

**offset:** `typing.Optional[int]` — Zero-based pagination offset.
    
</dd>
</dl>

<dl>
<dd>

**limit:** `typing.Optional[int]` — Maximum items to return (1–100).
    
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

Estimate the credit cost of running a workflow without creating a run.

Computes a breakdown of expected credits per node type based on the
workflow's current definition. No run is created, no credits are charged,
and no side effects occur. Equivalent to `POST /runs/preview`; prefer that
path in new integrations as it is co-located with the run lifecycle.
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

Dry-run credit estimate for a workflow — no run is created.

Returns a per-node-type credit breakdown based on the workflow's current
definition. No run is enqueued, no credits are charged, and the workflow
state is not modified. Use this before calling `POST /runs` to confirm
the expected cost. Equivalent to `POST /estimate`.
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

Aggregate run statistics for a workflow over an optional date window.

Returns per-status counts (`completed`, `failed`, `cancelled`, `pending`,
`running`, `paused`) plus two derived metrics:

- `pass_rate`: `completed / (completed + failed + cancelled)`. `null` when
  there are no terminal runs in the window.
- `average_duration_seconds`: mean of `completed_at - started_at` over
  successfully completed runs only. `null` when no runs have completed.

**Date range:** `from` / `to` filter by `created_at`. Both must be ISO 8601
with a UTC offset; a naive datetime returns 422. An inverted range
(`from > to`) also returns 422. Omit both to aggregate over all runs.

Use `GET /runs` with `?status=` filters for individual run details; this
endpoint is best for dashboard-style health metrics.
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

**from:** `typing.Optional[datetime.datetime]` — Filter runs by created_at >= this ISO datetime (ISO 8601 with UTC offset required).
    
</dd>
</dl>

<dl>
<dd>

**to:** `typing.Optional[datetime.datetime]` — Filter runs by created_at <= this ISO datetime (ISO 8601 with UTC offset required).
    
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

<details><summary><code>client.workflows.<a href="src/onepin/workflows/client.py">get_run_outputs</a>(...) -> ApiResponseWorkflowRunOutputsOut</code></summary>
<dl>
<dd>

#### 📝 Description

<dl>
<dd>

<dl>
<dd>

Fetch one logical output per sink node in a workflow run.

Every sink from the run's definition snapshot is returned in graph order,
including incomplete sinks with empty lines. Completed iterations are
unioned per sink with the latest completed value winning for duplicate
`line_id` values. Status reflects the latest attempt, so earlier completed
lines remain visible when a later attempt fails. Audio playback URLs are
short-lived and hydrated only on copied result lines.

Each sink's union is capped server-side; `truncated: true` on an output
signals that its `lines` are an incomplete prefix of the logical result.
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

client.workflows.get_run_outputs(
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

Returns structured metric sections (e.g. audio duration totals, validation
pass rates) grouped by display section, along with per-language audio
breakdowns and per-validator scoring summaries. Also includes a
`workflow_snapshot` with the graph definition and per-node completion states.

This endpoint is best suited for a summary/results view after a run
completes. It differs from the other run sub-resources as follows:

- `GET /runs/{run_id}` — full run record including the raw definition snapshot.
- `GET /runs/{run_id}/status` — volatile status fields only; for polling.
- `GET /runs/{run_id}/steps` — lightweight per-node step log by default;
  `include_result=true` includes results and audio playback URLs.
- `GET /runs/{run_id}/outputs` — one logical result per snapshot sink node.
- `GET /runs/{run_id}/data` — paginated script+audio rows for a data table.
- `GET /runs/{run_id}/overview` (this endpoint) — pre-aggregated metrics and
  node state map for a dashboard/overview panel.
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

Paginated script-and-audio data rows for a completed workflow run.

Returns grouped rows where each row represents one source script line.
Within each row, `cards` contain the per-language audio outputs, per-card
validation scores (word accuracy, naturalness), and short-lived audio
`playback_url` values (valid for 15 minutes).

**Filtering:**
- `search` narrows which rows are returned based on their source script text.
- `language` narrows the `cards` list within each returned row to a single
  locale. Rows with no matching cards are still returned (with empty `cards`),
  and `pagination.total` always reflects the search-filtered row count
  regardless of `language`.
- `include_dropped=true` adds rejected attempts to `cards` with
  `status="dropped"`; the default response remains delivered/generated data only.

**Pagination:** `pagination.total` is scoped to the `search` filter only.

Response includes a `partial` field indicating whether any data is still
being computed (e.g. audio not yet generated, validation not yet scored).
This endpoint sets `Cache-Control: no-store` because playback URLs are
short-lived and data may change while a run is still in progress.
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

**search:** `typing.Optional[str]` — Case-insensitive search over the source/script text of each row.
    
</dd>
</dl>

<dl>
<dd>

**language:** `typing.Optional[str]` — Exact full-locale code to filter cards within each row (e.g. `en-US`). `_` is normalized to `-`. Filtering is card-level only — rows remain visible even when all their cards are filtered out, and `pagination.total` is unaffected.
    
</dd>
</dl>

<dl>
<dd>

**include_dropped:** `typing.Optional[bool]` — Include validator-rejected audio cards reconstructed from unwired fail ports. Defaults to false so existing clients continue receiving delivered output only.
    
</dd>
</dl>

<dl>
<dd>

**offset:** `typing.Optional[int]` — Zero-based pagination offset.
    
</dd>
</dl>

<dl>
<dd>

**limit:** `typing.Optional[int]` — Maximum rows to return (1–100).
    
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

Create a temporary download URL for a complete workflow run export.

Returns a pre-signed URL pointing to a ZIP archive containing all audio
output files produced by the run. The URL is valid for 15 minutes
(`expires_at`). The archive is generated on first request and cached for
subsequent calls; re-calling this endpoint before expiry returns a new
URL for the same cached archive.

Only available for runs in `completed` status — returns 409 for runs that
are still active or ended in `failed`/`cancelled`. Returns 404 if the run
produced no audio files.

To download output from a single output node rather than the whole run,
use `GET /runs/{run_id}/nodes/{node_id}/download`.
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

<details><summary><code>client.workflows.<a href="src/onepin/workflows/client.py">get_run_audio_url</a>(...) -> ApiResponseDownloadUrlOut</code></summary>
<dl>
<dd>

#### 📝 Description

<dl>
<dd>

<dl>
<dd>

Mint a fresh playback URL for one audio output of a run.

`audio_id` is the stable 16-hex output identifier embedded in run-data
card ids and carried by assistant chat `audio` parts. Presigned playback
URLs expire after 15 minutes; call this endpoint at play time to refresh
the URL by id instead of caching it or re-fetching a whole run-data page.

Returns 404 when the run has no s3-backed audio output with this id.
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

client.workflows.get_run_audio_url(
    workflow_id="workflow_id",
    run_id="run_id",
    audio_id="audio_id",
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

**audio_id:** `str` 
    
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

Create a temporary download URL for a single output node's audio export.

Returns a pre-signed URL for a ZIP archive containing the audio files
produced by one specific output node within the run. Useful when a
workflow has multiple output nodes and the caller wants only one node's
results rather than the full run archive.

`node_id` must identify an output-category node in the run's definition
snapshot. Passing a node ID that belongs to a non-output node type (e.g.
an operator or validation node) returns 404. Returns 404 if the node
produced no audio files, and 409 if the run has not yet completed.

The URL is valid for 15 minutes. To download all output nodes in a single
archive, use `GET /runs/{run_id}/download` instead.
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

<details><summary><code>client.workflows.<a href="src/onepin/workflows/client.py">pause_run</a>(...) -> ApiResponseWorkflowRunOut</code></summary>
<dl>
<dd>

#### 📝 Description

<dl>
<dd>

<dl>
<dd>

Pause an active workflow run at the next safe checkpoint.

For a running run, the current wave of parallel nodes is allowed to finish
before the run parks (in-flight work is preserved, not abandoned). For a
pending run that has not yet started, it parks immediately. The run
transitions to `paused` status once drained; during the drain period,
`status` remains `running` with `pause_requested_at` set.

The operation is idempotent: pausing an already-paused run returns it
unchanged. A paused run can be resumed via `POST /runs/{run_id}/resume`
or permanently stopped via `POST /runs/{run_id}/cancel`.
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

client.workflows.pause_run(
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

<details><summary><code>client.workflows.<a href="src/onepin/workflows/client.py">resume_run</a>(...) -> ApiResponseWorkflowRunOut</code></summary>
<dl>
<dd>

#### 📝 Description

<dl>
<dd>

<dl>
<dd>

Resume a paused workflow run from its last completed wave.

Transitions the run from `paused` back to `running` and schedules
execution to continue from where it left off — no nodes that already
completed are re-executed.

Returns 409 if the workspace already has another active run for this
workflow, or if the caller is at the concurrent-run limit. In that case
the run stays `paused` and the caller can retry later. Only runs in
`paused` status can be resumed; attempting to resume a `running`,
`completed`, `failed`, or `cancelled` run returns 409.
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

client.workflows.resume_run(
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

<details><summary><code>client.workflows.<a href="src/onepin/workflows/client.py">duplicate_workflow</a>(...) -> ApiResponseWorkflowOut</code></summary>
<dl>
<dd>

#### 📝 Description

<dl>
<dd>

<dl>
<dd>

Create a copy of an existing workflow in the same workspace.

The new workflow inherits the source's `name` (suffixed with " (Copy)"),
`description`, and `definition`. Runs from the original workflow are not
copied — the duplicate starts with zero runs. Requires at least `editor`
role. Returns 201 with the new workflow on success.
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

List runs for a workflow, newest first by default.

Returns a counted, paginated list of runs for the specified workflow.
Each item includes the run's status, step progress (`total_steps`,
`finished_steps`), credit usage, and the actor who triggered it.

**Status filter:** Pass `?status=completed,failed` to OR-match multiple
statuses. Values must be the raw lowercase RunStatus strings. Unknown values
or empty tokens (e.g. `a,,b`) return 422.

**Pagination:** `pagination.total` reflects the filtered count. Sort
tiebreaks always append `id ASC` for stable offset/limit pagination.

For aggregate statistics (pass rate, average duration) across all runs,
use `GET /runs/summary` instead.
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

**offset:** `typing.Optional[int]` — Zero-based pagination offset.
    
</dd>
</dl>

<dl>
<dd>

**limit:** `typing.Optional[int]` — Maximum items to return (1–100).
    
</dd>
</dl>

<dl>
<dd>

**status:** `typing.Optional[str]` — Comma-separated raw RunStatus values (e.g. `completed,failed`). Values are case-sensitive lowercase: `pending`, `running`, `completed`, `failed`, `cancelled`, `paused`. Multiple values OR-match. Empty tokens (e.g. `a,,b`) and unknown values return 422.
    
</dd>
</dl>

<dl>
<dd>

**search:** `typing.Optional[str]` — Case-insensitive search over the triggering user's display name (falls back to email).
    
</dd>
</dl>

<dl>
<dd>

**sort:** `typing.Optional[ListRunsRequestSort]` — Sort field: `created_at` | `started_at` | `completed_at` | `status`. Defaults to `created_at`.
    
</dd>
</dl>

<dl>
<dd>

**order:** `typing.Optional[ListRunsRequestOrder]` — `asc` or `desc`. Defaults to `desc`.
    
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

Start a new execution of a workflow (202 Accepted).

Enqueues the workflow for asynchronous execution and returns the newly
created run in `pending` or `running` status. The run progresses through
its nodes in the background; poll `GET /runs/{run_id}/status` for
lightweight progress updates, or `GET /runs/{run_id}` once to load the
immutable definition snapshot.

The optional request body supplies run-scoped inputs: `script_text`
(and optionally `source_language`) replaces the source_script text for
THIS run's snapshot only — the stored workflow definition is not
modified, so concurrent runs with different scripts cannot race.
Requires exactly one source_script node (422 otherwise).

Use `POST /runs/preview` or `POST /estimate` to compute the credit cost
before committing to an actual run — those endpoints are read-only and
incur no charges.

Returns 409 if the workspace is at its concurrent-run limit or another
run for this workflow is already active.
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
from onepin import OnePinClient, WorkflowRunStartIn
from onepin.environment import OnePinClientEnvironment

client = OnePinClient(
    token="<token>",
    environment=OnePinClientEnvironment.PROD,
)

client.workflows.runs.start(
    workflow_id="workflow_id",
    request=WorkflowRunStartIn(),
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

**request:** `typing.Optional[WorkflowRunStartIn]` 
    
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

Fetch full detail for a single workflow run.

Returns all run fields plus `definition_snapshot` — the graph and
execution config captured at the moment the run started. The snapshot is
returned raw (no config migrations applied), so it faithfully represents
the workflow as it existed for this specific execution even if the
workflow definition has since been edited.

This is the heaviest run endpoint. For progress polling, use the lighter
`GET /runs/{run_id}/status` which omits the snapshot. For aggregated
visual metrics, use `GET /runs/{run_id}/overview`. For the per-node step
log, use `GET /runs/{run_id}/steps`; opt into full results and audio
playback URLs with `include_result=true`.
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

Lightweight run status for progress polling.

Returns only the volatile, frequently-changing fields: `status`, step
counts (`total_steps`, `finished_steps`), timestamps (`started_at`,
`completed_at`, `paused_at`, `pause_requested_at`), `usage_summary`,
`error`, and `has_export`. The definition snapshot is intentionally
omitted to keep response size small.

Recommended polling pattern: call `GET /runs/{run_id}` once after
starting a run to load the immutable definition snapshot and initial
metadata, then poll this endpoint until `status` reaches a terminal value
(`completed`, `failed`, or `cancelled`). `has_export` becoming `true`
signals that a download is ready via `GET /runs/{run_id}/download`.

The transient `pausing` state is observable here: `status == "running"`
with `pause_requested_at` set means a pause is in progress but the
current wave has not yet finished draining.
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

<details><summary><code>client.workflows.runs.<a href="src/onepin/workflows/runs/client.py">steps</a>(...) -> ApiResponseListWorkflowRunStepOut</code></summary>
<dl>
<dd>

#### 📝 Description

<dl>
<dd>

<dl>
<dd>

List per-node execution steps for a workflow run.

Returns one entry per node execution attempt, ordered by execution sequence.
By default, the response is lightweight: `result` is null, `has_result`
reports whether a stored result exists, and `active_ports` is projected from
the result without loading the full JSON payload.

Set `include_result=true` to restore the full result payload. Audio results
are then hydrated with short-lived `playback_url` values (valid for 15
minutes). `node_type` and `node_id` filters combine with AND semantics.

`node_display_name` is resolved from the run's definition snapshot, so it
reflects the name the node had when the run executed. Repeated executions of
the same node share that name and are distinguished by `iteration`.

For a higher-level view with aggregated metrics (pass rates, audio duration
by language), use `GET /runs/{run_id}/overview`. For paginated, grouped
script+audio rows suitable for a data table, use `GET /runs/{run_id}/data`.
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

client.workflows.runs.steps(
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

**include_result:** `typing.Optional[bool]` — Include the full step result payload and hydrate audio playback URLs.
    
</dd>
</dl>

<dl>
<dd>

**node_type:** `typing.Optional[NodeType]` — Filter steps by node type.
    
</dd>
</dl>

<dl>
<dd>

**node_id:** `typing.Optional[str]` — Filter steps by node ID.
    
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

Cancel an active workflow run.

Immediately marks the run as `cancelled` and stops any further processing.
In-flight work at the current node may be abandoned mid-execution. The
operation is idempotent: cancelling an already-cancelled run returns the
run unchanged without error.

Runs already in a terminal state (`completed`, `failed`, or `cancelled`)
are returned unchanged. Concurrent terminalization is also treated as an
idempotent success; a still-active compare-and-swap loser returns 409.

Unlike `pause`, cancel is permanent — a cancelled run cannot be resumed.
Use `pause` if you intend to continue the run later.
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

