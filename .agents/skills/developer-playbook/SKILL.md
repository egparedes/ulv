---
name: developer-playbook
description: |
  How the Developer implements a plan phase. Use when writing or editing
  code, tests, or docs for a planned feature ("build", "implement",
  "code this up", "make the tests pass"), or when the plan meets
  surprising reality. Method: comments and contracts first, strategic
  not tactical, escalate mismatches instead of diverging. Companion to
  the developer subagent and the /build command.
---

# Developer playbook

Working code isn't enough (PoSD): the deliverable is code a stranger can
read, change, and trust — plus the tests and docs that prove it. The
plan is the contract; reality is the judge; when they disagree you
escalate, never silently diverge.

Shared ground rules: `.agents/skills/design-principles/SKILL.md`.

## Method

1. **Write in the codebase's voice.** Match conventions, idioms, and
   comment density exactly (`development/style.md` and neighbouring
   code). Names come from `development/glossary.md` and the spec —
   naming drift is a defect, not a preference (DDD; PoSD).
2. **Interface comment before body.** For each new function or module,
   write the caller-facing comment first: what it does, its contract,
   never its implementation. If the comment comes out long or vague,
   the design is wrong — stop and reconsider before typing the body
   (PoSD: comments as design).
3. **Contracts on, crash early.** Turn stated invariants, pre- and
   postconditions into assertions that ship; impossible states abort
   loudly rather than limp on; whoever allocates frees. Implement the
   plan's error strategy exactly — no ad-hoc catch-and-log (PP).
4. **Test first against the contract.** The failing test states the
   behaviour; the code makes it pass; significant *states* get covered,
   not just lines. A bug found means a regression test written before
   the fix (PP: find bugs once).
5. **DRY across artifacts.** Code, tests, docs, and config must not
   restate the same knowledge divergently; when you change behaviour,
   hunt down every representation of the old truth in the same change
   (PP).
6. **Never program by coincidence.** Use documented behaviour only;
   prove what you assume (a quick REPL check beats a hopeful commit);
   read generated code before trusting it (PP).
7. **Leave it better — separately.** Fix broken windows you touch, but
   in refactor-only commits, never mixed into a behaviour change; if
   the cleanup outgrows the task, record it as a follow-up in
   `report.md` instead of a drive-by rewrite (PP; PoSD).
8. **Escalate plan/reality mismatches.** A module that can't stay deep,
   an assumption that fails, a phase that can't meet its exit criteria
   — stop, record it (`scratch.md` note for the Architect, or a
   `DECISION-PENDING:` line in `report.md` when it exceeds your
   authority), and hand back. Implementation strain is design feedback,
   and it is valuable precisely when it is fresh (DDD).
9. **Self-review before handoff.** Walk the red-flag checklist in
   `.agents/skills/design-principles/SKILL.md` over your own diff and
   fix what it catches, then re-run the gate if the fixes touched code.
   The Reviewer is for what you *can't* see, not for what you didn't
   look at.

## Gotchas

- "Read just enough context" means enough to make the change *safely* —
  the callers, the tests, the invariants — not just enough to make it
  compile.
- Green gate + ticked boxes is necessary, not sufficient: a phase whose
  code fails the red-flag pass isn't done, whatever the gate says.
- Honest reporting is a feature of your work product: deviations,
  dead ends, and surprises go in `report.md` when they happen, not
  reconstructed at the end.
