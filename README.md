# Unladen Velocity

[![CI](https://github.com/grAItools/ulv/actions/workflows/ci.yml/badge.svg)](https://github.com/grAItools/ulv/actions/workflows/ci.yml)

a Python tool for web-based visualization of performance benchmarks

## Quickstart

```sh
make test    # fast unit tests
make lint    # static checks
make fmt     # auto-format
make verify  # full gate; what the agent runs before claiming done
```

## Continuous integration

Every pull request and push to `main` runs the same gate across Python
3.12–3.14 on GitHub Actions, and PR titles are checked against
[Conventional Commits](development/style.md). Tagging `vX.Y.Z` builds the artifacts
and cuts a GitHub Release. See [ADR 0007](development/adr/0007-github-actions-ci.md)
for the design and the release runbook.

## AI coding agents

This repository follows the **agent-agnostic harness** convention:

- `AGENTS.md` is the canonical instruction file for every agent
  (Codex, OpenCode, Cursor, Amp, Factory, Gemini CLI, Copilot, …).
- `CLAUDE.md` is a one-line import of `AGENTS.md` plus Claude-Code-only
  stanzas (skills, subagents, slash commands, hooks).
- Shared agent assets (skills, subagents, and slash commands) live under
  `.agents/` and are symlinked into `.claude/` and `.opencode/`.
- Per-feature specs go under `development/work/<YYYY-MM>-<slug>/`.
- Architecture decisions are in `development/adr/` (Michael Nygard format, append-only).

See `AGENTS.md` for the full conventions.

## License

BSD-3-Clause
