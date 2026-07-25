
# Using the agentic harness (Claude Code & OpenCode)

`Unladen Velocity` ships a single agentic coding harness that both **Claude
Code** and **OpenCode** can drive. This guide explains how it is wired and how to
trigger the configured capabilities (subagents, slash commands, skills,
hooks) for different tasks — and how to phrase prompts so the existing `.agents/`
configuration is used without restating conventions every time.

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

`.agents/skills/` holds the four **role playbooks** (`{product-owner,architect,
developer,reviewer}-playbook`) plus the shared `design-principles` ground rules
they all link. Each role subagent reads its own playbook as part of its
instructions; the `verify` skill is separate — see below.

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

## The three ways capabilities get triggered

### 1. Manual (you type it)

- **Slash commands:** `/spec <slug>`, `/plan [dir]`, `/build [dir]`, `/verify`.
- **Skill by name:** "use the architect-playbook skill", "use the verify
  skill".
- **Subagent by name:** Claude Code — "use the explorer subagent to find where X
  is wired up"; OpenCode — `@explorer find where X is wired up` (the filename is
  the agent id).

### 2. Automatic by description match (the model decides)

Each subagent and skill has a `description` written as a _trigger_. When
your prompt matches that language, the capability fires without you naming it:

- The `verify` skill fires on "verify", "is this ready", "ready to commit",
  "check this", or after any non-trivial edit.
- The role playbooks fire on method cues — "how should I design this", "weigh
  the alternatives", "is this good" — independently of the slash commands.
- `explorer` fires on "find where X is implemented", "how does Y work", "what
  calls Z".
- The role agents fire on their phase cues (see [per-phase prompting](#writing-prompts-so-the-right-phase-config-is-used)).

### 3. Deterministic (the harness runs it, not the model)

Each tool runs format / block / verify behaviour outside the model's reasoning.
Both tools auto-format edited files through the same per-file entry point
(`scripts/fmt-file.sh`), so you never need to ask for formatting.
The mechanism and coverage differ per tool — see
[Claude Code specifics](#claude-code-specifics) and
[OpenCode specifics](#opencode-specifics).
The one gap to know: Claude Code also runs the full gate on Stop, whereas
OpenCode has no session-end gate, so under OpenCode you run `/verify` yourself
(CI is the backstop).

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
| Just run the gate and triage failures       | "verify" / verify skill   | —                 |
| Understand existing code before changing it | explorer (name / @)       | explorer          |
| One-off trivial fix (typo, one-liner)       | plain prompt, then verify | — (skip the loop) |

**Rule of thumb:** net-new feature → run the full loop; small isolated fix →
edit directly, then say "verify"; pure question about the code → explorer.

## Writing prompts so the right phase config is used

The agents are matched on description language. Phrase the request in that
language and the correct agent + output format is selected automatically.

### Phase 1 — Spec (product-owner)

- **Trigger words:** "new feature", "spec out", "I want to add…", or `/spec <slug>`.
- **What you get:** `spec.md` with Problem / Goal / Users & stakeholders /
  Success criteria / Non-goals / Constraints / Glossary / Open questions. WHAT
  and WHY only — no file paths or libraries.
- **Prompt tips:** Give the user-facing intent and at least one observable
  success condition. Don't prescribe implementation — the PO strips it.
- **Expect a dialogue, not one round.** The PO looks up whatever the repo can
  answer, then stops on the single highest-value question it still needs you
  for — with its own recommended answer attached, so "yes, go with that" is a
  valid reply. Answer it and the loop resumes; it writes the spec once nothing
  blocking is left (`/spec` caps this at five rounds). Repeated questions are
  the design working, not the agent stuck.

### Phase 2 — Plan (architect)

- **Trigger:** `/plan` after the spec is reviewed (defaults to most recent `development/work/*`).
- **What you get:** `plan.md` (Architecture-decisions block + numbered phases,
  each ≤1 day with explicit Tests and Exit criteria) and a mirrored checkbox
  `tasks.md`.
- **Prompt tips:** Run only once the spec is approved. New
  dependency/persistence/protocol choices are surfaced in the **Architecture
  decisions** block and flagged "ADR needed". It writes no code and stops.
- **Expect spike round-trips.** When the plan would rest on an untested
  assumption, the architect hands back a `SPIKE-REQUEST:` and the main agent
  runs a throwaway experiment (three rounds max), folding the findings into
  the plan's **Spike findings** section — so `/plan` may take a few
  hand-backs before `plan.md` appears. Spike code is disposable; only the
  findings survive.

### Phase 3 — Build (developer)

- **Trigger:** `/build` after the plan is approved.
- **Behaviour baked in:** works one phase at a time; **writes the failing test
  first** (tests are the spec); makes the smallest change to green; runs
  `make verify` at every phase boundary; ticks `tasks.md` in the same
  commit; **stops at each phase boundary** and asks you to `/verify` before
  continuing.
- **Prompt tips:** You usually just say `/build`. If the plan touches unfamiliar
  code, it runs an explorer pass first and drops notes in `scratch.md`. Don't ask
  it to "skip the test" — it refuses and drafts an ADR instead. It never edits
  `*/generated/*`.

### Phase 4 — Verify / review (reviewer)

- **Trigger:** `/verify`.
- **What you get:** a **GO / NEEDS-WORK** verdict across four axes — spec
  conformance (each criterion has observable evidence), plan conformance (no
  undocumented detours), implementation quality, and report honesty
  (`report.md` must match the code; undeclared deviations are defects) — plus
  a citation-rich defect list (`path/file.ext:LINE`) ranked MAJOR / MINOR /
  INFO. It re-runs the gate itself (it never takes the Developer's word), and
  it reads `plan.md`'s **Review checklist** as extra instructions. A red gate
  or any MAJOR is automatic NEEDS-WORK.
- **Loop back:** NEEDS-WORK → `/build` to fix; GO → ship/next phase. The reviewer
  is read-only — it never fixes, only reports.

### The `verify` skill vs the `/verify` command

These are distinct:

- **verify skill** = "run `make verify`, triage failures, propose
  smallest fix." Use mid-work: "verify", "is this ready". It does _not_ do the
  spec/plan review.
- **/verify command** = full reviewer pass against spec + plan + diff with a GO
  verdict. Use at a phase boundary.

## Document liveness

Which harness files may still change, and when they freeze. "Frozen" means
content-frozen: fixing a broken link in a sanctioned cleanup is fine; changing
what the document *says* is not.

| File | Liveness |
| --- | --- |
| `AGENTS.md`, `CLAUDE.md`, `development/*.md` | living, **trunk-gated**: changed via a dedicated PR (or an explicit maintainer request), never silently mid-feature. The two **registers** (last rows) accrete by their own contracts instead |
| `development/work/*/spec.md` | frozen once reviewed — scope changes get a new spec revision, noted in `report.md` |
| `development/work/*/plan.md` | frozen once `/build` starts — if the plan is wrong, hand back to `/plan`; don't edit it mid-build |
| `development/work/*/tasks.md` | living during build |
| `development/work/*/report.md` | frozen at merge — **never retro-edited**; new findings go in the report of the feature that finds them |
| `development/adr/NNNN-*.md` | frozen once accepted, except the Status line (supersede with a new ADR) |
| `development/adr/README.md` decision register | **register** — rows appended mid-feature (each `DECISION-PENDING:` marker lands with its row in the same PR), Status flipped in place |
| `development/glossary.md` | **register** — entries appended mid-feature only by promotion from a reviewed spec's **Glossary** section at `/spec` wrap-up (the Reviewer checks each new entry against that spec); renames and meaning changes are trunk-gated like prose |
| `development/work/*/scratch.md` | dead on completion (gitignored) |

## Conventions the agents already know (don't re-specify)

These are enforced by docs + hooks; restating them in prompts is noise:

- **Formatting** — automatic on edit (via `scripts/fmt-file.sh`); run
  `make fmt` to format the whole tree.
- **Verification gate** — `make verify` is the canonical lint + test gate
  (see `scripts/verify.sh`). Keep the fast loop (`make test`) under ~60s;
  slow suites belong in CI.
- **Tests are the spec** — a behaviour change means changing/adding a test first.
- **Commits** — Conventional Commits 1.0.0 in the **PR title** (squash-merge); branch commits can be freeform. See [`development/style.md#commit-messages`](style.md#commit-messages).
- **ADRs** — a significant decision may warrant an ADR in `development/adr/`
  (append-only); check the criteria in [`development/adr/README.md`](adr/README.md)
  before writing one — trivial or reversible choices get none. The architect flags
  candidates.
- **Working memory** — `scratch.md` is gitignored; promote durable notes into
  spec/plan/report/ADR/docs. `report.md` is the durable account of what
  actually happened (deviations, dead ends, follow-ups) and freezes at merge.
- **Decision escalation** — a decision beyond the agent's authority becomes a
  `DECISION-PENDING:` line in `report.md` plus a register row in
  [`development/adr/README.md`](adr/README.md), never a silent local fix.

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
"fix the off-by-one in the pagination helper"  → then  "verify"
```

Three habits that make the harness work for you:

1. Match the phase vocabulary ("spec", "plan", "build", "verify") so the right
   agent and output format are auto-selected.
2. Respect the stop boundaries — review each artifact before triggering the next
   phase.
3. Trust the deterministic behaviour — both tools auto-format on edit, so don't
   ask for formatting. The gate runs automatically on Stop in Claude Code;
   under OpenCode run `/verify` yourself before wrapping up (CI is the backstop).
