# Architecture Decision Records (ADRs)

One file per architecturally significant decision, named
`NNNN-kebab-title.md` (zero-padded to 4 digits, append-only).

## When to write one

Write an ADR only when **all three** are true:

1. **Hard to reverse** — the cost of changing your mind later is meaningful.
2. **Surprising without context** — a future reader will wonder "why did they
   do it this way?"
3. **The result of a real trade-off** — there were genuine alternatives and you
   picked one for specific reasons.

Most decisions fail at least one test and need no ADR: reversible, obvious, or
uncontested choices belong in the code, the commit message, or the plan — not
here. When in doubt, leave it out; you can add the ADR the day the trade-off
actually bites. A new datastore, wire protocol, or auth model usually clears all
three bars; a library swap you could undo in an afternoon usually does not. For
a one-line operational fact that clears none of the bars, a decision-register
row alone is enough (see "ADR or register row?" below).

## Format (Michael Nygard)

```markdown
# N. <Decision title>

## Status
<Proposed | Accepted | Deprecated | Superseded by ADR M>

## Context
<What is the issue we're seeing that is motivating this decision?>

## Decision
<What we're going to do.>

## Consequences
<What becomes easier, harder, or different as a result?>
```

Supersession adds a new ADR that references the old one; the only edit the
old file receives is flipping its Status line to `Superseded by ADR M` —
its body is never rewritten. The full historical record is the value.

Optional: install [`adr-tools`](https://github.com/npryce/adr-tools) (single
shell-script binary) and use `adr new "<title>"` to scaffold the next file
with the correct number.

## Decision register

One row per decision that an agent escalated (a `DECISION-PENDING:` line in a
feature's `report.md`) or that a human granted outside an ADR (a tolerance, a
pin, a one-line operational fact). Rows are appended and their Status flipped
in place (`pending` → `accepted` / `rejected`); nothing else is edited.

Contract: every `DECISION-PENDING:` line lands in the same PR as its register
row. After merge the report freezes, so the marker line stays as history and
**this register alone** records the outcome — to see what is still open, scan
the table for `pending` rows, not the reports. The reviewer checks the
contract per change: an escalation marker in the diff without a row here is
a defect.

A **marker** is narrower than the token. It is a line inside a
`development/work/*/report.md` that *begins* with the token followed by a
colon. The token written anywhere else — in these instruction files, in the
PR template, inside backticks, mid-sentence — is prose describing the
mechanism, not an escalation, and carries no register obligation. Without
that positional rule the contract flags its own documentation, and every PR
touching this file or `.agents/` inherits a defect for a marker that
escalates nothing.

| ID | Date | Decision | Status | Source | Evidence |
|---|---|---|---|---|---|
| 2026-07-template-v0.6.0.1 | 2026-07-25 | Relocate process memory to `development/` by hand before running `copier update`, rather than letting Copier's rename delete the project's own docs | accepted | [ADR 0010](0010-development-tree-and-process-memory.md) | this PR |
| 2026-07-template-v0.6.0.2 | 2026-07-25 | Move the five completed work units as-is; no back-filled `report.md` for features that merged under the previous contract | accepted | [ADR 0010](0010-development-tree-and-process-memory.md) | this PR |
| 2026-07-template-v0.6.0.3 | 2026-07-25 | Seed `development/glossary.md` once from `architecture.md` and `ulv.model`, bypassing the spec-promotion channel, because the vocabulary predates the register | accepted | [ADR 0010](0010-development-tree-and-process-memory.md) | this PR |

(ID = `<feature-slug>.<k>`, e.g. `2026-07-user-auth.1`. Source = the report
or ADR that raised it. Evidence = the PR/commit that settled it.)

**ADR or register row?** If the decision shapes structure — of the code, the
repo, or the process — and someone will later ask *why*, write an ADR and add
a register row whose Source points at it. If it is a one-line operational
fact, a register row alone is enough.
