# Continuous Integration with GitHub Actions

## Problem

Unladen Velocity has a strong local verification story — `make verify`
(`scripts/verify.sh`) runs lint, tests, docs-staleness, and a docs build, and a
Stop hook enforces it — but there is **no CI**: the repository contains no
`.github/` tree. Correctness therefore rests entirely on each contributor
remembering to run `make verify`, on whatever single Python version their local
`.venv` happens to be (currently 3.14). Nothing validates a pull request before
it merges, so a branch can land with a lint break, a stale generated CLI
reference, a broken docs build, or a PR title that violates the
Conventional-Commits convention the squash-merge model depends on. The project
declares `requires-python = ">=3.11"` but no version other than the developer's
is ever exercised.

Releases compound the problem. The v0.1.0 release was assembled entirely by
hand: manual `uv build`, hand-written release notes, and a manual
`gh release create`. Each release is bespoke, unrepeatable, and easy to get
wrong.

## Goal

Every push and pull request is automatically gated by the full existing
verification suite across the supported Python versions; PR titles are enforced
to the Conventional-Commits convention; and pushing a `vX.Y.Z` tag produces a
GitHub Release with no manual steps — with PyPI publishing ready to enable via a
single documented switch.

## Users & stakeholders

- **Primary users:** Contributors opening pull requests, who get automated,
  cross-version feedback instead of relying on a local gate.
- **Secondary users:** Maintainers cutting releases, who get repeatable
  tag-driven builds instead of hand assembly.
- **Stakeholders:** Maintainers responsible for release integrity and for the
  supply-chain posture of the CI itself.
- **Sign-off:** Repository maintainer (Enrique González Paredes).

## Success criteria

Each criterion becomes at least one verification step.

1. **The gate runs on every change.** A pull request or push that breaks
   `ruff check`, `ruff format --check`, a test, docs staleness, or the docs
   build fails CI and cannot show all-green.
2. **Cross-version coverage.** Tests run on Python 3.12, 3.13, and 3.14, and a
   failure on any single version is visible (matrix `fail-fast: false`).
3. **Lockfile fidelity.** CI uses `uv sync --locked`, so a run that has drifted
   from `uv.lock` fails rather than silently resolving different versions.
4. **PR titles are enforced.** A pull request whose title is not a valid
   Conventional-Commits header fails a dedicated check; a valid one passes. The
   accepted types match `docs/style.md`.
5. **Tag-driven releases.** Pushing a `vX.Y.Z` tag builds the sdist and wheel,
   smoke-installs the wheel and runs `ulv --version`, and publishes a GitHub
   Release whose body is the matching `CHANGELOG.md` section, with both
   artifacts attached.
6. **PyPI is scaffolded, not live.** A publish job exists, uses OIDC trusted
   publishing, carries no token secret, and stays inert until a documented
   repository variable is set.
7. **No drift between local and CI.** CI invokes the same `make` targets a
   developer runs locally; command strings are defined in one place, and
   `scripts/verify.sh` runs the same format check CI does. Dependabot keeps the
   pinned actions current.
8. **Releases are guarded against mismatch.** The release refuses to run unless
   the pushed tag, `pyproject.toml`'s `version`, and the `CHANGELOG.md` section
   header all agree, and the notes-slicer fails loudly rather than publishing an
   empty release body.

## Non-goals

- **Type-checking (mypy/pyright).** None is configured today; adopting it is a
  separate decision that warrants its own ADR.
- **Coverage gating.** No coverage tooling exists, and `docs/testing.md` treats
  coverage as "a smoke detector, not a goal." Not introduced here.
- **Live PyPI publishing.** Written and documented, but disabled until the PyPI
  project and a trusted publisher are configured out-of-band.
- **Branch-protection / required-checks configuration.** These are GitHub
  repository settings applied through the UI/API, not files in the repo; they
  are recorded as a follow-up, not automated.
- **Cross-OS matrix, container images, self-hosted runners.** Ubuntu-only.

## Decisions

1. **Mirror Make targets; do not inline commands.** CI calls `make lint`,
   `make fmt-check`, `make docs-check`, `make docs-build`, and `make test`. Two
   new targets (`fmt-check`, `docs-build`) are added so every CI step has a
   locally-runnable equivalent and each command string lives in exactly one
   place. `scripts/verify.sh` (the local/Stop-hook gate) also gains the
   `fmt-check` step, so the local gate and CI enforce the same set of checks.
   This is the core anti-drift decision.
2. **Split quality from the test matrix.** Lint, format-check, and docs run once
   on a single Python; only `pytest` fans out across 3.12–3.14, avoiding three
   redundant docs builds.
3. **Pin `uv` and pin actions.** `astral-sh/setup-uv` is used with an explicit
   `version:` and `enable-cache: true`; third-party actions are pinned (commit
   SHA preferred) and bumped by Dependabot. This mirrors the reproducibility the
   committed `uv.lock` already provides.
4. **PR-title lint is a dependency-free inline check.** A small stdlib-`re`
   script validates the title, which is passed via `env:` and never interpolated
   into a shell (avoiding script injection). This fits the repo's
   zero-dependency ethos; `amannn/action-semantic-pull-request` is the
   documented alternative.
5. **Least-privilege permissions.** The default token permission is
   `contents: read`; the release job elevates to `contents: write`, and
   `id-token: write` is granted only on the gated PyPI job.
6. **Enforce `ruff format --check` as blocking.** One file
   (`scripts/gen_cli_reference.py`) is currently unformatted — `make verify`
   never caught it because `verify.sh` runs no format check. Phase 1 reformats
   it first, after which the check is free. It is added to both CI and
   `scripts/verify.sh` so local and CI agree from day one.
7. **Align `requires-python` to `>=3.12`.** The tested matrix starts at 3.12, so
   the declared support floor is raised to match (with ruff
   `target-version = "py312"`), keeping the public claim honest. See Open
   question 1.

## Open questions

1. **Support floor.** Decision 7 raises `requires-python` to `>=3.12`. If 3.11
   support must be retained, the alternative is to add 3.11 back to the matrix
   instead of bumping the floor. Confirm before merge.
2. **Branch protection.** After merge, who configures the repository to require
   the CI checks and to restrict merges to squash? This is a GitHub setting,
   not a repo file.
