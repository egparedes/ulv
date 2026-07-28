
# Using the agentic harness (Claude Code & OpenCode)

`Unladen Velocity` ships a single agentic coding harness that both **Claude
Code** and **OpenCode** can drive. This guide explains how it is wired, which
capability to reach for, and where the two tools differ.

See also: [`AGENTS.md`](../AGENTS.md) (agent instructions),
[`CLAUDE.md`](../CLAUDE.md) (Claude Code specifics), [`development/style.md`](style.md),
[`development/testing.md`](testing.md), [`.agents/README.md`](../.agents/README.md)
(supported agents & how to add one).

## The shared model

The canonical definitions live once under `.agents/` and are symlinked into each
tool's config directory, so the same roles, commands, and skills serve every
tool. **You edit the files under `.agents/`, never the symlinks.**

```
.agents/subagents/  ─┬─►  .claude/agents/      .opencode/agents/      # 5 role agents
.agents/commands/   ─┼─►  .claude/commands/    .opencode/commands/    # /spec /plan /build /verify
.agents/skills/     ─┴─►  .claude/skills/      .opencode/skills/      # skills
```

`.agents/skills/` holds `design-principles` — the shared design ground rules
and red-flag checklist every role subagent reads before acting. Each role's
own method lives in its subagent file.

The design is a **gated four-phase loop** — one slash command per phase, each
backed by a single-purpose subagent that **stops for human review before the
next phase starts**:

```
idea ──/spec──▶ spec.md ──/plan──▶ plan.md + tasks.md ──/build──▶ code ──/verify──▶ GO / NEEDS-WORK
       PO              Architect                     Developer            Reviewer
      (write)          (write)                       (write+bash)         (read+bash)
```

Plus a read-only `explorer` agent any phase can call for codebase Q&A. Each
phase writes fixed artifacts under `development/work/<YYYY-MM>-<slug>/`.

The five subagents and their access:

| Subagent        | Writes? | Bash?                          | Job                                             |
| --------------- | ------- | ------------------------------ | ----------------------------------------------- |
| `product-owner` | yes     | no                             | author `spec.md`; stop before planning          |
| `architect`     | yes     | no                             | author `plan.md` + `tasks.md`; stop before code |
| `developer`     | yes     | yes                            | implement phase-by-phase, verify, tick tasks    |
| `reviewer`      | no      | read-only + verify/test/lint   | GO / NEEDS-WORK verdict, file:line defects      |
| `explorer`      | no      | read-only search/git           | "where is X / how does Y work" summaries        |

Subagents cannot spawn subagents, so a role that needs something run
outside itself stops mid-phase and **hands back**: the Product Owner
replies with one clarifying question at a time (you answer, the caller
re-invokes it), and the Architect / Developer append a
`HANDBACK(<spike|explore|replan>): …` line to the feature's `scratch.md`,
with the servicing instruction carried in their reply; results are
appended as `RESULT(<kind>): …` lines. The loops are bounded — three
spike hand-backs per plan, three explore hand-backs per phase, three
replan hand-backs per feature, five question rounds per spec — then
the question comes to you. A mid-phase stop is **not** a phase
boundary: read which stop it is before reaching for `/verify`.

## Claude Code specifics

Hooks and permissions are configured in `.claude/settings.json` (not symlinked;
Claude Code only). You cannot prompt around the hooks:

- **SessionStart** runs [`.agents/hooks/ensure-toolchain.sh`](../.agents/hooks/ensure-toolchain.sh)
  to **install** `uv` if it is missing. The installer adds it
  to your shell profile (so it is on PATH for *new* shells); a hook can't change
  the agent's already-running shells, so the `Stop` hook also exports it onto
  PATH for the verify gate.
- **PostToolUse (`Write|Edit|MultiEdit`)** runs `scripts/fmt-file.sh` on the
  edited file after every write.
- **PreToolUse (`Bash`)** hard-blocks `rm -rf`, `push --force`, `reset --hard`,
  `DROP TABLE` (exit 2) via [`.agents/hooks/block-destructive.sh`](../.agents/hooks/block-destructive.sh).
- **Stop** runs `make verify` before the agent is allowed to stop;
  non-zero blocks the stop. This is why "done" means "the gate is green".

Permissions allowlist the build tool, read-only git (`status/diff/log/show`),
and `rg/ls/cat/head/tail`; destructive operations are denied.
`.claude/rules/` holds path-scoped rule fragments (comment hygiene ships there). Default to
**plan mode** (`shift-tab`) for non-trivial work.

## OpenCode specifics

OpenCode reads `.opencode/opencode.jsonc`, which sets:

- **`instructions`** — loads [`AGENTS.md`](../AGENTS.md),
  [`development/architecture.md`](architecture.md), [`development/style.md`](style.md) as
  always-on context.
- **`default_agent: "build"`** — the session starts in the full-access `build`
  primary. OpenCode has two built-in **primary** agents, cycled with **Tab**:
  `build` (all tools) and `plan` (read-only: edits/bash set to `ask`). The five
  role agents above are **subagents**, reached via the slash commands or an
  `@mention`, not by Tab.
- **`permission.bash`** — allow/deny policy whose deny-list mirrors
  [`.agents/hooks/block-destructive.sh`](../.agents/hooks/block-destructive.sh).
- **`formatter`** — auto-format on edit (the analogue of Claude Code's
  PostToolUse format hook). It runs `scripts/fmt-file.sh` on the edited file so
  editor-time formatting is exactly what `make verify` enforces, and
  disables the conflicting built-in formatter to avoid double-formatting.

**Where OpenCode differs from Claude Code (so you rely on the right gate):**

- **No session-end verification gate.** OpenCode has no config-level "run on
  stop" hook, so there is nothing equivalent to Claude Code's `Stop` hook — run
  `/verify` **during** the session and rely on CI.
- **Destructive-bash blocking** uses `permission.bash` deny globs in `*…*`
  (substring) form that mirror `block-destructive.sh`'s patterns (`rm -rf`,
  `push --force`, `reset --hard`, `DROP TABLE`), so `cd x && rm -rf y` is caught.
  It's glob-not-regex and can't run a custom script, so for richer logic a
  `.opencode/plugin` with a `tool.execute.before` hook is the optional hardening.

| Capability             | Claude Code                              | OpenCode                                   |
| ---------------------- | ---------------------------------------- | ------------------------------------------ |
| Instructions           | `CLAUDE.md` (`@AGENTS.md`)               | `instructions` → `AGENTS.md` + docs        |
| Subagent invocation    | "use the X subagent"                     | `@mention` / auto-delegation (Task tool)   |
| Auto-format            | `PostToolUse` hook                       | native `formatter`                          |
| Verify gate            | `Stop` hook (blocking)                   | `/verify` + CI only (no session-end hook)  |
| Block destructive bash | `PreToolUse` hook (script)                 | `permission.bash` deny (`*…*` substring globs) |
| Path-scoped rules      | `.claude/rules/`                         | _(no equivalent)_                          |

## Browser automation (MCP)

The repo configures one MCP server, `playwright`
([Playwright MCP](https://github.com/microsoft/playwright-mcp), pinned
to `@playwright/mcp@0.0.78`, [ADR 0009](adr/0009-playwright-mcp-browser-automation.md)),
so agents can drive a real headless browser — needed for the
`ui-parity-check` skill, which exercises the `html-uplot` frontend's
canvas charts (coordinate mouse tools via `--caps=vision`).

- **Claude Code** reads [`.mcp.json`](../.mcp.json) at the repo root
  and **prompts you to approve** the server the first time a session
  uses it. Approve it, then the `browser_*` tools appear.
- **OpenCode** reads the `"mcp"` key in
  [`.opencode/opencode.jsonc`](../.opencode/opencode.jsonc); the
  server is enabled there, no separate approval file.
- **One-time setup:** the first `npx` use downloads the pinned package
  (network once, then cached), and the browser binary is installed
  once with `npx playwright install chromium`. Neither ever happens
  inside `make verify` — the gate has no browser, network, or MCP
  prerequisite.
- The two config files are kept in lockstep and version-pinned by
  `tests/test_harness_config.py`; bump both plus the test constant in
  one commit.
- A server only loads in sessions **started after** its config exists,
  so a fresh session is required the first time.

Invoke the check with "run the UI parity check" (or "frontend
regression check") after any change under
`src/ulv/outputs/html_uplot/static/`. The skill
(`.agents/skills/ui-parity-check/SKILL.md`) builds both fixture sites,
drives the 14-item parity checklist, and writes a per-item evidence
report (`development/work/<feature>/parity-report-<date>.md`, screenshots in the
gitignored `parity-evidence/`) with three-way verdicts for the owner's
sign-off review.

## Decision guide — which capability for which task

| If you want to…                             | Trigger                   | Backed by         |
| ------------------------------------------- | ------------------------- | ----------------- |
| Start a brand-new feature/bug/change        | `/spec <slug>`            | product-owner     |
| Turn an approved spec into a phased plan    | `/plan`                   | architect         |
| Implement an approved plan                  | `/build`                  | developer         |
| Review a finished phase / get a GO verdict  | `/verify`                 | reviewer          |
| Understand existing code before changing it | explorer (name / @)       | explorer          |
| One-off trivial fix (typo, one-liner)       | plain prompt, then verify | — (skip the loop) |

**Rule of thumb:** net-new feature → run the full loop; small isolated fix →
edit directly, then run `make verify`; pure question about the code →
explorer.

## Document liveness

Which harness files may still change, and when they freeze. "Frozen" means
content-frozen: fixing a broken link in a sanctioned cleanup is fine; changing
what the document *says* is not. This table is the harness's one full
liveness statement — other files link here.

| File | Liveness |
| --- | --- |
| `AGENTS.md`, `CLAUDE.md`, `development/*.md` | living, **trunk-gated**: changed via a dedicated PR (or an explicit maintainer request), never silently mid-feature. The two **registers** (last rows) accrete by their own contracts instead |
| `development/work/*/spec.md` | frozen once reviewed — scope changes get a new spec revision, noted in `report.md` |
| `development/work/*/plan.md` | frozen once `/build` starts — if the plan is wrong, hand back to `/plan`; don't edit it mid-build |
| `development/work/*/tasks.md` | living during build |
| `development/work/*/report.md` | frozen at merge — **never retro-edited**; new findings go in the report of the feature that finds them |
| `development/adr/NNNN-*.md` | frozen once accepted, except the Status line (supersede with a new ADR) |
| `development/adr/README.md` decision register | **register** — rows appended mid-feature (each `DECISION-PENDING:` marker lands with its row in the same PR), Status flipped in place |
| `development/glossary.md` | **register** — new entries only by promotion from a reviewed spec's Glossary section at `/spec` wrap-up (the rule lives in `glossary.md`); renames and meaning changes are trunk-gated like prose |
| `development/work/*/scratch.md` | dead on completion (gitignored) |

## Quick-start cheatsheet

```
# Net-new feature (full gated loop, review between each):
/spec my-feature        # PO → spec.md, stops
# (review spec.md)
/plan                   # Architect → plan.md + tasks.md, stops
# (review plan.md)
/build                  # Developer → implements phase 1, runs gate, stops
/verify                 # Reviewer → GO / NEEDS-WORK
/build                  # next phase (or fix NEEDS-WORK) … repeat

# Understand code first:
#   Claude Code: "use the explorer subagent to find where retries are handled"
#   OpenCode:    @explorer find where retries are handled

# Small fix, no ceremony:
"fix the off-by-one in the pagination helper"  → then run make verify
```

Three habits that make the harness work for you:

1. Match the phase vocabulary ("spec", "plan", "build", "verify") so the right
   agent and output format are auto-selected.
2. Respect the stop boundaries — review each artifact before triggering the next
   phase.
3. Trust the deterministic behaviour — both tools auto-format on edit, so don't
   ask for formatting. The gate runs automatically on Stop in Claude Code;
   under OpenCode run `/verify` yourself before wrapping up (CI is the backstop).
