# Tasks

Mirrors `plan.md`. Tick as you go; every phase ends with `make verify` green.

## Phase 1 — Foundation: Make targets + ADR

- [x] `make fmt` to reformat `scripts/gen_cli_reference.py` (currently fails
      `ruff format --check`); do this before wiring fmt-check into the gate
- [x] `Makefile`: add `fmt-check` (`uv run ruff format --check .`) and
      `docs-build` (`uv run zensical build`) targets with `##` help text; add
      both to `.PHONY`
- [x] `scripts/verify.sh`: add the `fmt-check` step so the local gate matches CI
- [x] `docs/adr/0007-github-actions-ci.md`: Nygard format; record
      mirror-Make-targets, pinned uv + actions, split jobs, least-privilege
      permissions, scaffolded PyPI + how to enable it later, release runbook
- [x] `make fmt-check`, `make docs-build`, `make verify` (fmt-check included)
      green

## Phase 2 — Core CI workflow (`ci.yml`)

- [x] `on: push (main) + pull_request`; `permissions: contents: read`;
      `concurrency` per ref with `cancel-in-progress`
- [x] `quality` job (Python 3.12): setup-uv pinned + cache +
      `python-version: '3.12'` → `uv sync --locked` → `make lint` →
      `make fmt-check` → `make docs-check` → `make docs-build`; add an
      actionlint workflow-lint job
- [x] `test` job matrix `['3.12','3.13','3.14']`, `fail-fast: false`, setup-uv
      with `python-version: ${{ matrix.python }}` → `uv sync --locked` →
      `make test`; confirm cells run distinct interpreters
- [x] `pyproject.toml`: `requires-python = ">=3.12"`, ruff
      `target-version = "py312"` (confirmed); `uv.lock` re-locked
- [x] `actionlint` (installed binary) clean on ci.yml
- [x] `make verify` green

## Phase 3 — PR-title enforcement (`pr-title.yml`)

- [x] `on: pull_request` (opened/edited/synchronize/reopened);
      `permissions: contents: read`
- [x] stdlib regex check; title via `env:` (no shell interpolation); type list
      matches `docs/style.md`; helpful failure message
- [x] Bad title fails, valid title passes; metacharacter title cannot execute
- [x] `actionlint` (installed binary) clean

## Phase 4 — Release automation + Dependabot

- [x] `release.yml` `on: push tags v*.*.*` **and** `workflow_dispatch`;
      `permissions: contents: write` (PyPI job restates only `id-token: write`)
- [x] `guard`: assert tag == `pyproject.toml` version == CHANGELOG header; fail
      loudly on mismatch
- [x] `build`: `uv build` → upload `dist/*`
- [x] `smoke`: download artifact, install wheel in clean env, run `ulv --version`
- [x] `github-release`: slice matching `## [x.y.z]` CHANGELOG block (exit
      non-zero on no match) → `gh release create` attaching `dist/*`
- [x] `pypi-publish`: OIDC trusted publishing, guarded
      `if: vars.PYPI_PUBLISH == 'true'`, no secrets
- [x] `.github/dependabot.yml`: github-actions ecosystem, weekly
- [x] `scripts/release_notes.py` + `tests/test_release_notes.py` (slicer
      fails loudly on missing/empty section)
- [x] `actionlint` clean on all workflows; dry-run path validated locally
      (slicer + regex unit-tested; live PR/tag pass is a documented follow-up)

## Phase 5 — Docs, changelog, follow-ups

- [x] `CHANGELOG.md` `[Unreleased]`: CI + release automation; Python-floor and
      verify-gate changes
- [x] `README.md`: CI status badge + CI/contributing pointer
- [x] Branch-protection follow-up recorded in spec Open questions
- [x] `tasks.md` reflects final state
- [x] `make verify` green
