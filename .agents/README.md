# Agent harness

This directory holds the **cross-tool** agent definitions — `subagents/`,
`commands/`, and `skills/` — that are symlinked into each tool's own directory
(`.claude/`, `.opencode/`) so they are defined once and read by all. `hooks/`
holds shared hook scripts (see the deny-list note below).

The governing rule: **root [`AGENTS.md`](../AGENTS.md) is the single source of
truth for agent instructions. Wire every agent to it by reference — never
duplicate content.** Each agent has its own convention for where it looks for
project-level instructions; copying the same guidance into a Claude file, a
Gemini file, a Cursor file, and so on makes the copies drift. Pointing every
agent back at one file prevents that structurally.

## Supported agents

| Agent                                                               | How it reads the instructions                      | Wiring in this repo                                                               |
| ------------------------------------------------------------------- | -------------------------------------------------- | --------------------------------------------------------------------------------- |
| Claude Code                                                         | `CLAUDE.md` (first line `@AGENTS.md`) + `.claude/` | `CLAUDE.md`, `.claude/settings.json`, `.claude/{agents,commands,skills}` symlinks |
| OpenCode                                                            | `.opencode/opencode.jsonc` `instructions`          | `.opencode/opencode.jsonc`, `.opencode/{…}` symlinks                              |
| GitHub Copilot                                                      | coding agent: native root `AGENTS.md`; code review: `.github/` files only | populated `.github/copilot-instructions.md` + `.github/instructions/` review rules + `.github/skills/code-review/` skill (opt-in `copilot_code_review`; code review does **not** read `AGENTS.md`) |
| OpenAI Codex                                                        | native root `AGENTS.md` (32 KiB doc cap)           | none needed                                                                       |
| Google Gemini CLI                                                   | `.gemini/settings.json` `context.fileName`         | add `.gemini/settings.json` → `AGENTS.md` (see recipe below)                      |
| Jules, Cursor, Windsurf, Roo Code, Zed, JetBrains Junie, Aider, Amp | native root `AGENTS.md`                            | none needed                                                                       |
| Cline, Continue                                                     | a `*-rules/` dir of plain `.md`                    | not wired; see recipe below                                                       |

## Adding an agent

1. **Reads root `AGENTS.md` natively?** Do nothing but add a row above.
2. **Reads a plain-markdown file at a fixed path (no required frontmatter)?**
   Symlink it to `AGENTS.md` with a relative target, like the existing symlinks:
   ```sh
   # examples for rules-directory agents
   ln -s ../AGENTS.md    .clinerules/AGENTS.md
   ln -s ../../AGENTS.md .continue/rules/AGENTS.md
   ```
3. **Needs a config key or a frontmatter'd file?** Add a thin pointer/config stub
   that references `AGENTS.md`. Never copy instruction prose into it. Precedent:
   ```jsonc
   // .gemini/settings.json
   { "context": { "fileName": ["AGENTS.md", "GEMINI.md"] } }
   ```
4. Put tool-specific guidance (not meant for every agent) in that tool's own file,
   not in `AGENTS.md`.

## Layout

Everything here is a single source read by both tools. The symlinks are
created by the post-generation hook; if you copy this layout manually,
recreate them with:

```sh
ln -s ../.agents/subagents .claude/agents    && ln -s ../.agents/subagents .opencode/agents
ln -s ../.agents/commands  .claude/commands  && ln -s ../.agents/commands  .opencode/commands
ln -s ../.agents/skills    .claude/skills    && ln -s ../.agents/skills    .opencode/skills
```

### `subagents/`

One Markdown file per role, with YAML frontmatter. Supported keys:

- `name` (required) — invocation name; identity comes from this, not the
  filename.
- `description` (required) — used by parent agents to decide when to
  delegate; start with "Use proactively when…" for auto-discovery.
- `model` (optional) — `sonnet` / `opus` / `haiku` / `inherit`.
- `tools` (optional) — Claude Code allowlist, comma-separated names
  (e.g. `Read, Grep, Glob, Bash`). Claude Code only.
- `permission` (optional) — OpenCode per-action map with keys
  `read` / `write` / `edit` / `bash`, each taking `allow` / `ask` / `deny`;
  `bash` can also be a per-pattern map (e.g. `"rg *": allow`, `"*": deny`).
  OpenCode only — Claude Code ignores this field.
- `mode` (optional, **strongly recommended for subagents**) — OpenCode-only.
  Set `mode: subagent` to keep the agent delegation-only; the default
  (`all`) would also expose it as a top-level primary OpenCode agent.

A subagent runs in its own context window — use them to keep heavy
exploration or repetitive review out of the main session's context. Claude
Code subagents **cannot spawn other subagents**: when a role needs something
run outside itself (an `explorer` pass, a spike experiment, a user's
answer), it stops and hands back to the main agent, carrying the request
and the resume instruction in its own reply — the role subagents' Handoff
sections define these protocols. The reply must be self-contained because a
subagent can be reached by description match as well as by its slash
command, and in the former case the command's instructions were never
loaded.

### `commands/`

One Markdown file per slash command, with YAML frontmatter (`description`,
optional `argument-hint`). Keep each command short and imperative — the
description is what surfaces in the slash-command picker, and the body is
the prompt the agent will follow.

### `skills/`

One directory per skill, containing a `SKILL.md` (required, with YAML
frontmatter `name` and `description`) and optionally `scripts/`
(deterministic executables), `references/` (docs loaded on demand), and
`assets/`. `design-principles/` is the skill that ships — the shared design
ground rules and red-flag checklist the role subagents read. Write skill
descriptions slightly "pushy" — agents tend to under-trigger skills —
and include synonyms.

## Caveats

- **Copier-managed.** This harness is generated from a Copier template
  (`gh:grAItools/harness-copier-template`; see `.copier-answers.yml`). Edits to
  template-owned files (`.claude/settings.json`, `.opencode/opencode.jsonc`,
  `AGENTS.md`, the managed `.gitignore` block) can be reverted by `copier update`;
  port durable changes upstream behind a per-agent toggle. Net-new files (this
  README, `.agents/hooks/*`, `.gemini/settings.json`) are safe.
- **Symlinks need `core.symlinks=true`.** On Windows checkouts without it, Git
  materializes a symlink as a text file containing the target path; prefer a stub
  there. The repo already relies on symlinks for `.claude/` / `.opencode/`.
- **Destructive-command deny-list** is canonical in
  [`hooks/block-destructive.sh`](hooks/block-destructive.sh); OpenCode's deny globs
  are a hand-kept mirror (it cannot call a script).
- **Hook payload parsing** is canonical in
  [`hooks/hook-input.sh`](hooks/hook-input.sh): the Claude Code hooks in
  `.claude/settings.json` read their JSON input through it (`jq`, with a
  `python3` fallback). With neither parser on PATH, the PreToolUse guard fails
  closed with an explanatory message and SessionStart prints a warning.
