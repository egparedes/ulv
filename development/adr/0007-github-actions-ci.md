# 7. GitHub Actions CI

## Status

Accepted

## Context

The project had a strong local verification gate (`make verify` /
`scripts/verify.sh`, enforced by a Stop hook) but no continuous integration:
the repository contained no `.github/` tree. Correctness therefore depended on
each contributor remembering to run the gate, on whatever single Python version
their local environment happened to provide, and nothing validated a pull
request before merge. The v0.1.0 release was assembled entirely by hand (manual
`uv build`, hand-written notes, manual `gh release create`), making releases
unrepeatable.

We want automated, cross-version gating on every pull request and push, PR-title
enforcement for the squash-merge model, and repeatable tag-driven releases,
without duplicating logic that could drift from the local gate.

## Decision

- **Provider: GitHub Actions**, Ubuntu-only. The repository is already on
  GitHub; no cross-OS or self-hosted requirement exists.
- **Mirror Make targets, do not inline commands.** CI invokes `make lint`,
  `make fmt-check`, `make docs-check`, `make docs-build`, and `make test`. Two
  new non-mutating targets (`fmt-check`, `docs-build`) are added so every CI
  step has a locally-runnable equivalent and each command string lives in one
  place. `scripts/verify.sh` also gains the `fmt-check` step so the local gate
  and CI enforce the same checks.
- **Split quality from the test matrix.** Lint, format-check, and docs run once
  on Python 3.12; only `pytest` fans out across a `['3.12','3.13','3.14']`
  matrix (`fail-fast: false`), with `python-version` pinned per cell so each
  runs a distinct interpreter.
- **Pin the toolchain.** `astral-sh/setup-uv` with an explicit `version:` and
  `enable-cache: true`; `uv sync --locked` to fail on lockfile drift;
  third-party actions pinned (commit SHA preferred) and maintained by Dependabot
  (`github-actions` ecosystem). Workflows are linted with `actionlint` (the Go
  binary — `uvx actionlint` does not resolve).
- **Enforce Conventional-Commits PR titles** via a dependency-free stdlib check;
  the title is passed through `env:` and validated in a Python step, never
  interpolated into a shell (injection-safe). Accepted types match
  `development/style.md`.
- **Least-privilege permissions.** Default `contents: read`; the release job
  elevates to `contents: write`, and the PyPI job additionally sets
  `id-token: write`. Note GitHub *replaces* rather than merges a job's
  `permissions`.
- **Tag-driven releases** (`on: push tags v*.*.*` plus `workflow_dispatch` for
  dry runs): a `guard` job asserts the tag, `pyproject.toml` `version`, and the
  `CHANGELOG.md` section header agree; `build` runs `uv build`; `smoke` installs
  the wheel and runs `ulv --version`; `github-release` slices the matching
  changelog section (failing loudly on no match) and creates the release.
- **PyPI publishing is scaffolded but disabled.** The publish job uses OIDC
  trusted publishing (no stored secret) and is guarded by
  `if: vars.PYPI_PUBLISH == 'true'`, so it stays inert until enabled.
- **Align `requires-python` to `>=3.12`** (ruff `target-version = "py312"`) to
  match the tested matrix.

## Consequences

- Every pull request is gated across three Python versions; a lint, format,
  test, or docs regression cannot merge green.
- The local gate and CI cannot silently diverge: they run the same targets, and
  `verify.sh` now includes the format check (one previously-unformatted file,
  `scripts/gen_cli_reference.py`, was reformatted when this landed).
- Releases become a single action: push a `vX.Y.Z` tag and a verified GitHub
  Release is produced. The guard prevents shipping a mismatched wheel or an
  empty release body.
- The declared support floor rises to Python 3.12; 3.11 is no longer supported.

### Release runbook

Before tagging a release: (1) bump `version` in `pyproject.toml`; (2) promote
the `CHANGELOG.md` `[Unreleased]` section to `## [x.y.z] — <date>` with a fresh
empty `[Unreleased]` above it and a compare link; (3) push the `vx.y.z` tag. The
`guard` job rejects the release if these disagree.

### Enabling PyPI publishing later

(1) Register the `unladen-velocity` project on PyPI; (2) configure a trusted
publisher for this repository and the `release.yml` workflow (PyPI → project →
Publishing); (3) set the repository variable `PYPI_PUBLISH=true`. No token
secret is stored — publishing authenticates via OIDC.
