---
description: Implement the current feature one phase at a time, ticking tasks.md and running the verification gate at each phase boundary
argument-hint: <spec-dir-name> (optional; defaults to the most recent development/work/* directory)
---

You are carrying out the implementation phase of a feature.

1. Identify the target spec directory.
   - If `$ARGUMENTS` is provided, use `development/work/$ARGUMENTS/`.
   - Otherwise, use the most recently modified directory under
     `development/work/`.
2. Read `spec.md`, `plan.md`, and `tasks.md` in full. If `plan.md` is
   missing or empty, stop and tell the user to run `/plan` first.
3. If the plan touches an unfamiliar area of the codebase, run an
   `explorer` subagent pass first to summarise the relevant code
   paths, and put the summary in `scratch.md` for the Developer to
   read. (The Developer is itself a subagent and cannot spawn the
   `explorer` subagent on its own.)
4. Delegate the work to the **developer** subagent
   (`.agents/subagents/developer.md`). In the delegation prompt,
   tell it to read `scratch.md` first if you populated it in
   step 3 — that is where the explorer summary lives, and the
   Developer's required-reading rule already covers it when present.
   The developer will then:
   - Work one phase at a time, writing tests first where the plan
     calls for behaviour change.
   - Tick `tasks.md` checkboxes in the same commit as the code change.
   - Keep `report.md` current: deviations, abandoned approaches, and
     `DECISION-PENDING:` escalations are recorded when they happen.
   - Run `make verify` at every phase boundary.
   - Stop at the end of each phase and hand off to `/verify`
     (Reviewer) before starting the next.
5. If the developer stops mid-phase, that is not a phase boundary. Its
   reply names the stop and the servicing instruction; follow it:
   - `HANDBACK(explore):` in `scratch.md` — run the `explorer`, append
     its answer as a `RESULT(explore):` line (keep the `path:LINE`
     citations), then re-invoke the developer. After three explore
     hand-backs on the same phase, the phase is scoped too wide — stop
     and put it to the user.
   - `DECISION-PENDING:` in `report.md` — put the question to the user,
     add the register row (`development/adr/README.md`), re-invoke the
     developer with the answer.
   - `HANDBACK(replan):` in `scratch.md` — hand back to `/plan`
     (Architect), then re-run `/build`. After three replan hand-backs
     on the same feature, the plan and reality are not converging —
     stop and put the mismatch to the user instead of re-planning.
6. When the developer reports a phase complete, **stop** and ask the
   user to run `/verify`. Do not auto-start the next phase.

Never silently skip a failing test, edit anything under `*/generated/`,
or run destructive Git.
