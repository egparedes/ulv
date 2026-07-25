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
contract per change: a `DECISION-PENDING:` line in the diff without a row
here is a defect. (The marker is the colon form, `DECISION-PENDING:`;
mentions of the token without the colon are prose, not markers.)

| ID | Date | Decision | Status | Source | Evidence |
|---|---|---|---|---|---|

(ID = `<feature-slug>.<k>`, e.g. `2026-07-user-auth.1`. Source = the report
or ADR that raised it. Evidence = the PR/commit that settled it.)

**ADR or register row?** If the decision shapes structure — of the code, the
repo, or the process — and someone will later ask *why*, write an ADR and add
a register row whose Source points at it. If it is a one-line operational
fact, a register row alone is enough.
