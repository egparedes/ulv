# Plan

Implements `spec.md` (approved). The design principle is **parity, not drift**:
CI invokes the same `make` targets a developer runs locally, so the two cannot
diverge. Ubuntu-only, `uv`-driven. Each phase ends with `make verify` green
(workflows do not affect the local gate, but the convention holds). Because
GitHub Actions cannot run locally, every workflow phase is additionally
validated with `actionlint` (the installed binary — **not** `uvx actionlint`,
which does not resolve) and, before the feature is called done, with an
end-to-end pass on a scratch pull request and tag
(see `## End-to-end verification`).

Reference points: the four gate steps in `scripts/verify.sh:33-36`, the Make
targets in `Makefile`, the toolchain notes in `docs/tool-bootstrap.md`, the
merge convention in `docs/style.md:83-88`, and the `## [x.y.z] — date`
changelog section format already used in `CHANGELOG.md`.

## Architecture decisions

- **New ADR 0007 — GitHub Actions CI.** Records the mirror-Make-targets
  principle, pinned `uv` + pinned actions, the split quality/matrix jobs,
  least-privilege permissions, and scaffolded-but-disabled PyPI trusted
  publishing. ADR needed.
- **Two new Make targets** (`fmt-check` → `uv run ruff format --check .`,
  `docs-build` → `uv run zensical build`). No runtime-dependency impact; both
  are non-mutating so CI can call them safely. `scripts/verify.sh` gains the
  `fmt-check` step too, so the local/Stop-hook gate matches CI (closes the
  drift gap the format check would otherwise open). ADR: n/a.
- **Metadata alignment**: `requires-python = ">=3.12"` and ruff
  `target-version = "py312"` (spec Decision 7, confirmed). ADR: n/a.
- **Workflow linting**: validated with `actionlint`. `uvx actionlint` does
  **not** resolve (actionlint is a Go binary, not a PyPI package); use the
  official install script / pinned binary locally, and run
  `rhysd/actionlint` (or `reviewdog/action-actionlint`) as a step inside
  `ci.yml` so workflows are linted in CI too. ADR: n/a.

## Phase 1 — Foundation: Make targets + ADR

**Scope.** Add the two Make targets CI depends on, make the format check pass,
wire it into the local gate, and record the decision — no workflows yet, so the
phase is self-contained and fully verifiable locally.

**Steps.**
1. Reformat the one offending file first: `make fmt` (reformats
   `scripts/gen_cli_reference.py`; confirm no behavioral diff — it only touches
   formatting). This must precede step 3, or the local gate goes red.
2. `Makefile`: add `fmt-check:` (`uv run ruff format --check .`) and
   `docs-build:` (`uv run zensical build`) with `##` help text; add both to the
   `.PHONY` line.
3. `scripts/verify.sh`: add a `run "fmt-check" uv run ruff format --check .`
   step (alongside the existing four) so the local/Stop-hook gate enforces the
   same format check as CI (spec Decision 1 / criterion 7).
4. Write `docs/adr/0007-github-actions-ci.md` in Nygard format (Status Accepted
   / Context / Decision / Consequences) capturing the decisions above, the
   documented steps to enable PyPI later, and the release runbook (bump
   `version`, promote `[Unreleased]`, then tag).

**Tests.** `make fmt-check` passes; `make docs-build` builds `_site/`; both are
idempotent and leave no tracked changes. `make verify` now includes fmt-check
and is green.

**Exit criteria.** `make fmt-check`, `make docs-build`, and `make verify`
(fmt-check included) all green.

## Phase 2 — Core CI workflow (`.github/workflows/ci.yml`)

**Scope.** The pull-request/push gate: one `quality` job plus a `test` matrix.

**Steps.**
1. `on:` `push` to `main` and `pull_request`. Top-level
   `permissions: contents: read`. `concurrency:` keyed by ref with
   `cancel-in-progress: true`.
2. `quality` job (ubuntu-latest, Python 3.12): checkout → `astral-sh/setup-uv`
   (pinned `version:`, `enable-cache: true`, `python-version: '3.12'`) →
   `uv sync --locked` → `make lint` → `make fmt-check` → `make docs-check` →
   `make docs-build`. Include a workflow-lint step (`rhysd/actionlint`) so the
   workflows lint themselves in CI.
3. `test` job (`strategy: { fail-fast: false, matrix: { python:
   ['3.12','3.13','3.14'] } }`): checkout → setup-uv with
   `python-version: ${{ matrix.python }}` (this exports `UV_PYTHON`, so each
   cell genuinely runs a different interpreter — without it `uv sync` could
   silently reuse one Python and defeat criterion 2) → `uv sync --locked` →
   `make test`.
4. Align metadata (spec Decision 7, confirmed): set `requires-python = ">=3.12"`
   and ruff `target-version = "py312"` in `pyproject.toml`.

**Tests.** `actionlint .github/workflows/ci.yml` is clean (installed binary,
not `uvx`). On a scratch PR, all three matrix cells run on distinct Python
versions (verify in the job logs); a deliberately introduced lint / format /
test / docs break turns the corresponding check red and is then reverted.

**Exit criteria.** Workflow lints clean; green on a no-op PR; `make verify`
green locally.

## Phase 3 — PR-title enforcement (`.github/workflows/pr-title.yml`)

**Scope.** Enforce Conventional-Commits PR titles for the squash-merge model.

**Steps.**
1. `on: pull_request` (`types: [opened, edited, synchronize, reopened]`),
   `permissions: contents: read`.
2. One job passing `${{ github.event.pull_request.title }}` through `env:` into
   a stdlib `python` step that validates it against
   `^(feat|fix|docs|refactor|test|chore|build|ci|perf|style|revert)(\(.+\))?!?: .+`
   and exits non-zero with a message citing `docs/style.md` on mismatch.

**Tests.** A scratch PR titled `broken title` fails; retitled `ci: add pipeline`
it passes. A title containing shell metacharacters cannot execute — it reaches
Python only through the environment.

**Exit criteria.** Both cases behave; `actionlint` (installed binary) clean.

## Phase 4 — Release automation + Dependabot

**Scope.** Tag-driven GitHub Release, wheel smoke-test, scaffolded PyPI, and
action-version maintenance.

**Steps.**
1. `.github/workflows/release.yml`, `on:` both `push: tags: ['v*.*.*']` and
   `workflow_dispatch:` (the dry-run path the tests below use). Top-level
   `permissions: contents: read`; only the `github-release` job elevates to
   `contents: write`, and only `pypi-publish` sets `id-token: write` — note
   GitHub *replaces* rather than merges a job's `permissions`, so each elevated
   job restates just the scope it needs (github-release: contents; pypi:
   id-token). Jobs:
   - `guard` (runs first): assert the pushed tag, `pyproject.toml`'s `version`,
     and the `CHANGELOG.md` section header all agree; fail loudly on any
     mismatch so a `v0.2.0` tag can't ship a `0.1.0` wheel or an empty release
     body. Skipped/parameterized under `workflow_dispatch`.
   - `build`: checkout → setup-uv → `uv build` → upload `dist/*` as an artifact.
   - `smoke`: download the artifact, install the built wheel into a clean
     environment, and run `ulv --version`, asserting the console script and
     shipped static tree work from the artifact.
   - `github-release`: slice the matching `## [x.y.z]` block out of
     `CHANGELOG.md` with a small script that **exits non-zero on no match**,
     then `gh release create` (using `GITHUB_TOKEN`) attaching `dist/*`.
   - `pypi-publish`: `pypa/gh-action-pypi-publish` via OIDC, guarded by
     `if: vars.PYPI_PUBLISH == 'true'` so it stays inert (unset → empty string →
     skipped) until enabled. No secrets.
2. `.github/dependabot.yml`: the `github-actions` ecosystem, weekly, to keep the
   pinned actions current.

**Tests.** `actionlint` clean. A dry run via `workflow_dispatch` (now a real
trigger) or a throwaway `v0.0.0-rc1` tag on a scratch branch exercises
guard + build + smoke + release-notes slicing without touching PyPI; confirm the
guard fails on a deliberate version/tag mismatch and the notes-slicer fails on a
missing changelog section; confirm the PyPI job is skipped while the variable is
unset.

**Exit criteria.** A tag produces a GitHub Release with the correct notes and
both artifacts; the guard blocks mismatched tags; the PyPI job is present and
skipped; the Dependabot config is valid.

## Phase 5 — Docs, changelog, follow-ups

**Scope.** Make the new surface discoverable and record the manual follow-ups.

**Steps.**
1. `CHANGELOG.md` `[Unreleased]`: one bullet noting CI + release automation,
   leading with the behaviour per `docs/style.md`.
2. `README.md`: a CI status badge and a one-line pointer to the CI/contributing
   flow.
3. Record the branch-protection follow-up (require the `quality` + matrix
   checks; restrict merges to squash) in the spec's Open questions — it is a
   GitHub setting, not a repo file.
4. Fill `tasks.md` to mirror these phases.

**Tests.** `make docs-build` still green; README links resolve.

**Exit criteria.** `make verify` green; spec, plan, and tasks consistent.

## Risks & open questions

- **Workflows cannot be fully validated locally.** Mitigation: `actionlint` in
  every phase plus a scratch PR/tag pass before the feature is called done.
- **The `requires-python` bump is a public metadata change.** Mitigation:
  flagged as spec Open question 1; trivially reversible by re-adding 3.11 to the
  matrix instead of raising the floor.
- **Runner assumptions (`uv`, `git`, network).** Low risk — GitHub runners
  provide `uv`/`git`, and all tests bind loopback only. Mitigation: pin `uv`
  and use `uv sync --locked`.
- **Third-party action supply chain.** Mitigation: SHA-pin third-party actions
  and let Dependabot propose bumps.
- **Release-time human error** (tag without bumping `version` or promoting
  `[Unreleased]`). Mitigation: the `guard` job and the fail-loud notes-slicer
  block the release; the runbook lives in ADR 0007.

## End-to-end verification

1. Open a PR from a scratch branch; confirm `quality` and all three matrix
   cells run and pass. Introduce a temporary lint/format/test/docs break,
   confirm the matching check goes red, then revert.
2. Title the PR non-conventionally → the PR-title check fails; retitle to a
   valid `ci: …` header → it passes.
3. Push a throwaway `v0.0.0-rc1` tag (or use the `workflow_dispatch` trigger) to
   exercise `release.yml`: verify guard + build + wheel smoke (`ulv --version`) +
   release-notes slicing, confirm the guard rejects a deliberate tag/version
   mismatch, and confirm the PyPI job is skipped. Delete the test release/tag
   afterward.
