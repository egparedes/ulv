# Unladen Velocity — Agent Instructions

A Python tool for web-based visualization of performance benchmarks

## Stack

- Language: **python**
- Package / build manager: **uv**
- License: BSD-3-Clause
- Tool versions, install steps, and new-machine setup:
  see [`development/tool-bootstrap.md`](development/tool-bootstrap.md).

## Commands (prefer these over guessing)

- `make test` — fast unit tests (= `uv run pytest -q`)
- `make lint` — static checks (= `uv run ruff check .`)
- `make fmt`  — auto-format (= `uv run ruff format .`)
- `make verify` — full verification gate

If a command above is wrong for your environment, **fix the Makefile**, not
this file.

## Where things live (capabilities, not paths)

- Architecture overview: [`development/architecture.md`](development/architecture.md)
- Driving the harness (Claude Code & OpenCode): [`development/harness-usage.md`](development/harness-usage.md)
- Style guide: [`development/style.md`](development/style.md)
- Testing strategy: [`development/testing.md`](development/testing.md)
- ADRs (decisions of record): [`development/adr/`](development/adr/)
- Per-feature specs: [`development/work/<YYYY-MM>-<slug>/`](development/work/)
- Supported agents & how to add one: [`.agents/README.md`](.agents/README.md)

## Do

- `uv` is bootstrapped automatically at session start by
  [`.agents/hooks/ensure-toolchain.sh`](.agents/hooks/ensure-toolchain.sh); if you
  land in a bare shell without it, run that script (details in
  [`development/tool-bootstrap.md`](development/tool-bootstrap.md)).
- Run `make verify` before claiming a task is done.
- For a net-new feature, follow the four-phase loop:
  `/spec` (Product Owner) → `/plan` (Architect) → `/build` (Developer)
  → `/verify` (Reviewer). Each phase stops for review before the next
  begins. See `.agents/commands/` and `.agents/subagents/`.
- For a new architectural choice (dependency, framework, persistence, auth),
  add an ADR in `development/adr/`. ADRs are append-only; supersede with a new file.
- When investigating a large codebase, prefer the `explorer` subagent (read-only)
  over loading large files into the main context.

## Don't

- Don't edit anything under `*/generated/` — it's overwritten by your project's codegen pipeline.
- Don't add a runtime dependency without an ADR.
- Don't run destructive Git: `push --force`, `reset --hard origin/*`,
  history rewrites on shared branches.
- Don't put secrets, hostnames, or per-developer paths in this file —
  they belong in a git-ignored file (e.g `AGENTS.local.md` or `CLAUDE.local.md`).
- Don't auto-generate or expand this file beyond ~200 lines. The instruction
  budget is finite; adding rules degrades adherence to *all* rules.

## Conventions

- Code style: see `development/style.md`. One worked example > a page of prose.
- Comments describe the code, not the process: explain *why*, keep them
  accurate, no review/release-process prose. See
  [`development/style.md`](development/style.md#comments).
- Tests are the spec. If you change behaviour, change a test first.
- Commit messages: **Conventional Commits 1.0.0** — apply the format to the **PR title** (squash-merge).
  See [`development/style.md`](development/style.md#commit-messages) for the format,
  type list, breaking-change syntax, examples, and full merge-strategy
  guidance.
- Changelog: if the project keeps a `CHANGELOG.md`, log user-facing changes
  under `[Unreleased]` as one concise bullet each, leading with the
  file/behaviour. See [`development/style.md`](development/style.md#changelog).
- Branch names: `<initials>/<slug>` for personal branches; bare slug for
  shared feature branches.

## Working memory

Per-feature spec directories use this layout:

```
development/work/<YYYY-MM>-<slug>/
├─ spec.md     # WHAT and WHY; no implementation detail
├─ plan.md     # numbered phased plan; each phase has tests
├─ tasks.md    # checkbox list the agent ticks off
└─ scratch.md  # agent's working notes; cleared on completion (gitignored)
```

`scratch.md` is gitignored by default. Promote anything durable into `spec.md`,
`plan.md`, an ADR, or `docs/`.
