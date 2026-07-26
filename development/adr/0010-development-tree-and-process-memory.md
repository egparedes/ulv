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
a per-feature `report.md`, a decision register, and a glossary.

Adopting the move by running `copier update` directly would have been
destructive. Copier models a template-side rename as delete-then-create, and
`_skip_if_exists` protects only paths that already exist at the destination.
A dry run against a throwaway clone confirmed the outcome: this repo's
178-line `architecture.md` deleted and replaced by the template's 32-line
`_Fill in:_` scaffold, the Browser-automation section lost from
`harness-usage.md`, ADRs 0002–0009 stranded in `docs/adr/` while `AGENTS.md`
pointed agents at `development/adr/`, and the five completed work units left
in `specs/` while the slash commands defaulted to an empty `development/work/`.

## Decision

Relocate the tree by hand *first*, then run `copier update`, so the template
sees a destination already in its new shape and `_skip_if_exists` preserves
the project's own content instead of overwriting it.

- `docs/{architecture,style,testing,tool-bootstrap,harness-usage}.md` and
  `docs/adr/` → `development/`. ADR numbering is continuous: 0001–0009 keep
  their numbers and their cross-references.
- `specs/<slug>/` → `development/work/<slug>/`. The five completed work units
  move as they are and get no back-filled `report.md`: they merged under the
  previous contract, and a report reconstructed after the fact would be
  fiction in a document whose whole value is honesty.
- `development/glossary.md` is seeded once from `architecture.md` and
  `ulv.model`, because the vocabulary predates the register. Its normal
  channel — promotion from a reviewed spec's Glossary section — applies from
  the next feature on.
- `docs/` keeps only `docs/user/`, which is what `zensical.toml` publishes.

## Consequences

- Agents get one tree to look in, and every harness path in `AGENTS.md`,
  `CLAUDE.md`, and the slash commands resolves. ~119 references across 44
  files were rewritten to match.
- Future `copier update` runs are cheap: the destination shape now matches the
  template's, so the skip-list does its job.
- New obligations from v0.6.0 apply to work starting from here: `report.md` as
  a work-unit deliverable, `DECISION-PENDING:` escalations paired with rows in
  the decision register, and the three-criteria ADR test — which is stricter
  than the rule it replaces ("don't add a runtime dependency without an ADR"),
  so some future dependency choices will get a register row instead of an ADR.
- The relocation is a breaking change for anything that referenced the old
  paths from outside this repo — bookmarks, issue links, external docs. The
  git history preserves the old paths; nothing else does.
- `.opencode/opencode.jsonc` is now known to be a file Copier will overwrite
  on update, taking the Playwright MCP block with it. `tests/test_harness_config.py`
  catches that, but the restore is manual each time.
