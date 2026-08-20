# 10. Process memory lives in development/, docs/ is user documentation

## Status

Accepted

## Context

Until now `docs/` held two unrelated things: the agent-facing harness
documents that came from the copier template (`architecture.md`, `style.md`,
`testing.md`, `tool-bootstrap.md`, `harness-usage.md`, `adr/`) and the
user-facing site that `zensical.toml` publishes from `docs/user/`. Per-feature
work units lived in a third top-level directory, `specs/`.

Template v0.6.0 separates the two: harness documents and work units move to
`development/`, and `docs/` is reserved for user documentation the way `src/`
is reserved for sources. It also adds three things this repo had no place for —
a per-feature `report.md`, a decision register, and a glossary. This repo
adopted the move as part of the v0.5.0 → v0.7.0 template update.

Copier models the template-side rename as delete-then-create: `copier update`
deleted the template-owned files at their old paths (including this repo's
178-line `architecture.md`) and generated fresh scaffolds under
`development/`. The project's own content was recovered by rendering pristine
v0.5.0 and v0.7.0 copies of the template, diffing them against the tree to
separate local customizations from template boilerplate, and restoring or
migrating each piece in the same commit.

## Decision

Adopt the template's split, and migrate the repo's own content into it:

- `docs/{architecture,style,testing,tool-bootstrap,harness-usage}.md` and
  `docs/adr/` → `development/`. ADR numbering is continuous: 0001–0009 keep
  their numbers and their cross-references.
- `specs/<slug>/` → `development/work/<slug>/`. The five completed work units
  move as they are and get no back-filled `report.md`: they merged under the
  previous contract, and a report reconstructed after the fact would be
  fiction in a document whose whole value is honesty.
- Path references are rewritten everywhere they occur — live files and the
  migrated work units alike. Navigability wins over historical-path purity:
  the documents remain frozen in substance, but a pointer that no longer
  resolves misleads the next agent that follows it.
- `development/glossary.md` is seeded once from `architecture.md` and
  `ulv.model`, because the vocabulary predates the register. Its normal
  channel — promotion from a reviewed spec's Glossary section — applies from
  the next feature on.
- `docs/` keeps only `docs/user/`, which is what `zensical.toml` publishes.

## Consequences

- Agents get one tree to look in, and every harness path in `AGENTS.md`,
  `CLAUDE.md`, and the slash commands resolves.
- Future `copier update` runs are cheap: the destination shape now matches
  the template's.
- New obligations from v0.6.0 apply to work starting from here: `report.md`
  as a work-unit deliverable, `DECISION-PENDING:` escalations paired with
  rows in the decision register, and the three-criteria ADR test. This repo
  keeps its stricter standing rule for one class of decision: a runtime
  dependency always gets an ADR (see `AGENTS.md`), the register bar governs
  the rest.
- The relocation is a breaking change for anything that referenced the old
  paths from outside this repo — bookmarks, issue links, external docs. The
  git history preserves the old paths; nothing else does.
- In this update copier's three-way merge preserved the hand-added Playwright
  MCP block in `.opencode/opencode.jsonc`; that is merge behaviour, not a
  guarantee. `tests/test_harness_config.py` pins both MCP configs so a future
  update that drops the block fails the gate instead of shipping.
