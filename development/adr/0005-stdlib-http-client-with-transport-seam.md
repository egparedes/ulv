# 5. Stdlib HTTP client with an injectable transport seam

## Status

Accepted

## Context

Spec Decision 1 puts fetching results from a Bencher server in scope:
read-only, paginated GETs against `/v0/projects/{project}/reports`,
optionally authenticated with a bearer token. The project ships with
zero runtime dependencies; `httpx` or `requests` would be the first,
bought for features this workload doesn't use (connection pooling,
async, retries, sessions). Tests must never touch the live network,
and the API token must never leak into error messages or logs.

## Decision

- Use `urllib.request` behind a minimal transport seam: any object
  with `get(url, headers) -> (status, body_bytes)` satisfies it.
  `UrllibTransport` is the default; tests inject fakes (canned pages,
  error statuses) through the input format's options or constructor,
  and one integration test runs the real transport against a local
  `http.server` stub — no live network anywhere in the suite.
- Token sourcing: `--bencher-token` flag > `bencher_token` config key
  > `BENCHER_API_TOKEN` env var (the env var is the recommended
  channel; the flag exists for setting-parity and leaks into shell
  history, which its help text says).
- Token hygiene: the token travels only in the `Authorization`
  header, never in URLs; error messages name the endpoint URL and
  status only, and the fetcher defensively scrubs the token string
  from any `UlvError` text passing through it.
- Failure contract: non-2xx statuses (401/403 get an explicit
  authentication message), malformed payloads, and runaway pagination
  raise `UlvError` naming the endpoint. The fetch completes fully
  before generation starts, so the generator's atomic-output contract
  keeps a partial fetch from ever emitting a site.

## Consequences

- Zero runtime dependencies stands.
- No HTTP/2, retries, or connection reuse — irrelevant for a
  batch fetch of a few hundred small JSON pages; revisit only if a
  real deployment shows otherwise.
- The seam makes the Phase 10 test matrix (pagination, auth failures,
  malformed payloads, token-absence-in-errors) plain unit tests.
- Recorded response fixtures are hand-modeled from Bencher's public
  OpenAPI document rather than a live server; the seam makes a
  recorded-against-live refresh a drop-in.
