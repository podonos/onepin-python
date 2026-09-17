"""Server-side result gates -- filters that change what an empty result means.

An ordinary filter narrows a list and the caller knows it did: they asked for
``--gender female`` and got female voices. A *gate* is different in two ways that make it
unsafe to ship as one more :class:`~onepin._cli._spec.Opt`:

1. **It can be dropped without an error.** FastAPI ignores a query parameter it does not
   declare, so an older deployment answers ``?buildable=true`` with ``200`` and the *full*
   catalog. The failure mode is not a stack trace, it is a correct-looking list that the CLI
   would then describe as filtered. Every gate therefore has to prove the server honors it
   before the CLI says it did -- :func:`BuildableGate.probe`.
2. **It moves the denominator.** The gate narrows ``pagination.total`` along with the page,
   so "0 of 0" under a gate does not mean "this locale has no voices". Saying which of the
   two happened is the gate's job, not the reader's -- :func:`BuildableGate.report`.

Everything a gate prints goes to **stderr**, in both human and ``--json`` mode: the ``--json``
stdout contract is a bare array pinned by the manifest snapshot, and an agent that has to be
told the gate was applied should not have to accept a changed payload shape to hear it.
"""

from __future__ import annotations

import enum
from dataclasses import dataclass
from typing import Any, Mapping, Optional, Sequence

from onepin._cli._ctx import CliError
from onepin._cli.render import echo_warning

#: Query parameter and 422 ``details[].field`` name the API uses for the buildable gate.
_BUILDABLE_PARAM = "buildable"

#: ``details[].reason`` the API answers with when ``buildable`` arrives without ``language``.
_REQUIRES_LANGUAGE = "requires_language"


class Support(enum.Enum):
    """What the CLI managed to learn about a server's support for a gate.

    ``UNKNOWN`` is a real answer, not an error: the probe could not reach a verdict (network
    blip, an auth failure, an unexpected status). It is kept distinct from ``NO`` because the
    two warrant opposite handling -- a known-unsupported server must not be asked for a gated
    list at all, while an unverified one may be, as long as nobody claims the gate applied.
    """

    YES = "yes"
    NO = "no"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class ProbeResult:
    """A capability verdict plus the reason, so an ``UNKNOWN`` can explain itself."""

    support: Support
    detail: str = ""


class BuildableGate:
    """``voices list --buildable``: only voices the server could synthesize for ``--language``.

    The gate carries the eligibility half of automatic voice selection onto the browse list:
    a measured ``(provider, model, locale)`` above the quality floors, on an enabled and
    routable provider/model that is billable (or covered by the workspace's own BYOK key).
    Voices the workspace owns are exempt -- nothing measures a customer's own upload.

    What it deliberately does **not** cover is transient provider health. A vendor whose
    circuit breaker is open still lists, because excluding it would empty a whole locale on a
    blip. So a buildable voice is one nothing *structural* rules out, not one guaranteed to
    render: :meth:`report` is worded to keep that promise small.
    """

    name = "buildable"
    param = _BUILDABLE_PARAM

    #: Probe verdicts, keyed by (base_url, workspace). Process-local and never written to
    #: disk: which voices are buildable turns over with provider routing and must not be
    #: remembered between invocations, and whether the *server* knows the parameter is a
    #: property of a deployment the user can repoint at any moment with --base-url.
    _probe_cache: dict[tuple[str, str], ProbeResult] = {}

    @staticmethod
    def is_on(kwargs: Mapping[str, Any]) -> bool:
        """True when the caller actually switched the gate on for this invocation."""
        return bool(kwargs.get(_BUILDABLE_PARAM))

    @classmethod
    def probe(cls, creds: Any, workspace_id: Optional[str], *, timeout: float = 10.0) -> ProbeResult:
        """Ask the server whether it knows ``buildable``, by using the parameter's own precondition.

        There is no cheaper honest signal available. This deployment serves no OpenAPI document
        (``/openapi.json`` is behind ``ENABLE_DOCS`` and off in production) and advertises no
        server version, so neither of the usual capability checks can run -- but the parameter
        is self-identifying: a server that declares ``buildable`` **rejects** it without
        ``language`` (``422``, ``details[0] = {"field": "buildable", "reason": "requires_language"}``),
        and a server that does not declare it ignores the whole thing and answers ``200``. So one
        deliberately incomplete request separates them exactly.

        Args:
            creds: Resolved credentials (``api_key`` + ``base_url``).
            workspace_id: Workspace to scope the probe to, so it is evaluated where the real
                call will be.
            timeout: Probe timeout in seconds.

        Returns:
            A :class:`ProbeResult`. Anything other than the two decisive shapes is ``UNKNOWN``
            -- the real request is about to be made anyway and will report its own failure.
        """
        import httpx

        from onepin._cli._http import _user_agent

        base_url = (getattr(creds, "base_url", None) or "https://api.onepin.ai").rstrip("/")
        cache_key = (base_url, workspace_id or "")
        cached = cls._probe_cache.get(cache_key)
        if cached is not None:
            return cached

        headers = {
            "Authorization": f"Bearer {getattr(creds, 'api_key', '') or ''}",
            "User-Agent": _user_agent(),
        }
        if workspace_id:
            headers["X-Workspace-Id"] = workspace_id
        # limit=1 because an old server answers this with a real page and there is no reason
        # to make it build a big one just to tell us it ignored the flag.
        params = {_BUILDABLE_PARAM: "true", "limit": "1"}

        try:
            with httpx.Client(timeout=timeout) as client:
                response = client.get(f"{base_url}/api/v1/voices", params=params, headers=headers)
        except httpx.HTTPError as exc:
            result = ProbeResult(Support.UNKNOWN, f"the check could not reach {base_url} ({type(exc).__name__})")
        else:
            result = cls._verdict(response)

        cls._probe_cache[cache_key] = result
        return result

    @classmethod
    def _verdict(cls, response: Any) -> ProbeResult:
        """Read one probe response into a verdict."""
        status = response.status_code
        if status == 422:
            try:
                body = response.json()
            except ValueError:
                return ProbeResult(Support.UNKNOWN, "the check got an unreadable 422")
            if requires_language_detail(body):
                return ProbeResult(Support.YES)
            # A 422 about something else (a bad key shape, a missing header) says nothing
            # about `buildable` -- it never got as far as being judged.
            return ProbeResult(Support.UNKNOWN, "the check was rejected for an unrelated reason")
        if status == 200:
            # The parameter was sent, the precondition was not enforced, a page came back:
            # the server does not declare `buildable` and silently dropped it.
            return ProbeResult(Support.NO)
        return ProbeResult(Support.UNKNOWN, f"the check returned HTTP {status}")

    @classmethod
    def preflight(cls, creds: Any, workspace_id: Optional[str]) -> ProbeResult:
        """Verify the gate before the real request, refusing to fetch a list that would be ungated.

        Raises:
            CliError: If the server is known not to support the gate. Returning the full
                catalog under a flag that asked for a subset is the one outcome worth failing
                for -- it is indistinguishable from success at the call site.
        """
        result = cls.probe(creds, workspace_id)
        if result.support is Support.NO:
            raise CliError(
                "BUILDABLE_UNSUPPORTED",
                "This Onepin API does not support --buildable: it ignores the parameter and "
                "returns the full catalog, which would look like a filtered one. Re-run without "
                "--buildable to browse everything, or upgrade the API this CLI points at.",
            )
        return result

    @classmethod
    def report(cls, result: ProbeResult, *, shown: int, languages: Sequence[str]) -> None:
        """Say what the returned rows now mean. Always stderr; never touches the payload."""
        locales = ", ".join(languages) if languages else "the requested locale"

        if result.support is Support.UNKNOWN:
            echo_warning(
                f"--buildable could not be confirmed on this server ({result.detail}). "
                "Treat this list as UNFILTERED: an API that does not know the parameter drops "
                "it and answers with the whole catalog."
            )
            return

        if shown == 0:
            echo_warning(
                f"No buildable voices for {locales}. This is the --buildable gate, not an empty "
                "catalog -- it narrows pagination.total as well as the page, so the 0 total does "
                "not describe the catalog. Re-run without --buildable to see every voice for "
                f"{locales}."
            )
            return

        echo_warning(
            f"--buildable is on: these are the voices this API could route a synthesis to for "
            f"{locales} at the time of the call, and pagination.total counts only those. "
            "Transient provider outages are deliberately not part of the check, so a run can "
            "still fail -- and buildability moves with provider routing, so do not store this "
            "as a lasting property of a voice."
        )

    @classmethod
    def translate_error(cls, exc: Exception) -> Optional[CliError]:
        """Turn the gate's own 422 into a sentence, or return None to leave the error alone.

        The client-side ``requires=("--language",)`` check stops the obvious case, but not the
        one where ``--language`` was passed and *none* of its values resolved to a locale the
        server supports: the gate has nothing to judge against and answers with the same 422.
        The raw envelope names a ``field`` and a ``reason`` and no next step, so it is replaced
        rather than forwarded.
        """
        if getattr(exc, "status_code", None) != 422:
            return None
        if not requires_language_detail(getattr(exc, "body", None)):
            return None
        return CliError(
            "BUILDABLE_REQUIRES_LANGUAGE",
            "--buildable needs at least one --language value the server recognizes, and none of "
            "the ones passed resolved to a supported locale. `onepin --json voices facets` lists "
            "the language values that exist.",
        )


def requires_language_detail(body: Any) -> bool:
    """True if an API error body carries the gate's ``buildable``/``requires_language`` detail.

    Tolerant by design: this reads a *foreign* error envelope, and every shape that is not the
    one signature we are looking for has to answer False rather than raise -- it is used both
    to classify a probe response and to decide whether to rewrite a real error.
    """
    if not isinstance(body, dict):
        return False
    error = body.get("error")
    details = error.get("details") if isinstance(error, dict) else body.get("details")
    if not isinstance(details, list):
        return False
    return any(
        isinstance(detail, dict)
        and detail.get("field") == _BUILDABLE_PARAM
        and detail.get("reason") == _REQUIRES_LANGUAGE
        for detail in details
    )


#: Gates by the name a :class:`~onepin._cli._spec.Cmd` row declares in ``gate=``.
GATES: dict[str, type[BuildableGate]] = {BuildableGate.name: BuildableGate}


def get_gate(name: Optional[str]) -> Optional[type[BuildableGate]]:
    """Resolve a declared gate name to its handler, or None when the row declares none."""
    if name is None:
        return None
    gate = GATES.get(name)
    if gate is None:
        raise CliError("INTERNAL", f"Unknown gate {name!r}")
    return gate
