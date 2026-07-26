---
description: Expand spec.md into a numbered, testable plan.md for the current feature
argument-hint: <spec-dir-name> (optional; defaults to the most recent development/work/* directory)
---

You are expanding a feature spec into an implementation plan.

1. Identify the target spec directory.
   - If `$ARGUMENTS` is provided, use `development/work/$ARGUMENTS/`.
   - Otherwise, use the most recently modified directory under
     `development/work/`.
2. Confirm `spec.md` exists and has been reviewed. If it's missing or
   empty, stop and tell the user to run `/spec` first.
3. Delegate the planning to the **architect** subagent
   (`.agents/subagents/architect.md`). It owns the phased-plan format,
   the architecture-decisions block, the "each phase has tests"
   contract, and the "stop and ask before coding" boundary.
4. If the architect hands back a **spike request** — a
   `SPIKE-REQUEST:` line in `scratch.md` naming one question (it cannot
   run code itself) — run the smallest throwaway experiment that answers
   it, in a temp dir or scratch space, never left in the source tree.
   Append the result to `scratch.md` on a `SPIKE-FINDING:` line
   (question → method → answer → evidence), then re-invoke the
   architect; it starts with fresh context and reads `scratch.md` to
   pick the answer up. Spike code is disposable; only the findings
   survive, in the plan's **Spike findings** section.
   Cap this at **three rounds per plan**. A fourth request means the
   uncertainty is not a design experiment — stop and put the question
   to the user.

The architect subagent will write `plan.md` and mirror it into
`tasks.md`, then stop for user review. Once the user confirms the
plan, the next step is `/build` (Developer role). Do not start
implementing yet.
