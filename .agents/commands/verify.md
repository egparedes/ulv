---
description: "Critically review the current diff against spec/plan and run the verification gate (make verify), producing a GO / NEEDS-WORK verdict"
---

You are running the review phase for the current feature.

Delegate the work to the **reviewer** subagent
(`.agents/subagents/reviewer.md`). It will:

- Read `spec.md`, `plan.md` (including its **Review checklist**
  section, if present), `tasks.md`, `report.md` (if the Developer has
  started it — expected by the final phase), and the current diff.
- Run `make verify` itself — it never takes the Developer's
  word for the gate.
- Check spec conformance, plan conformance, implementation quality,
  and report honesty (undeclared deviations are defects).
- Produce a `GO` or `NEEDS-WORK` verdict with a citation-rich defect
  list (`path/to/file.ext:LINE`), ranked MAJOR / MINOR / INFO. Any
  MAJOR means NEEDS-WORK.

Hand the reviewer's verdict back to the user verbatim. If
`NEEDS-WORK`, the next step is `/build` (Developer role) to address
the defects. If `GO` on the feature's final phase, confirm `report.md`
is complete (what was built, deviations, negative results, follow-ups,
gate result) before the feature is declared mergeable — it freezes at
merge. Then summarise what changed since the last verify (use
`git diff --stat` and `git log -1`) and stop.

Never silently skip, disable, or `@ignore` a failing test. If a test
must be skipped, draft an ADR under `development/adr/` and ask for
confirmation.
