# Plan

> Example work unit. Written by `/plan` (Architect) after `spec.md` is
> reviewed; frozen once `/build` starts. The sections mirror the
> Architect's output format in `.agents/subagents/architect.md`.

## Architecture decisions

- <Decision>: <chosen option> — <one-line rationale>.
  Considered: <rejected option> — <one-line why it lost>.
  ADR: <link, "ADR needed: <topic>", or "n/a">.

## Spike findings

- <Question> → <answer>. Method: <what was run>. Evidence: <output>.
  (Omit the section if no spikes were needed.)

## Phase 1 — <name>

**Scope.** <One paragraph.>

**Steps.**
1. <Concrete step>
2. <Concrete step>

**Tests.** <Which test(s) prove this phase works.>

**Exit criteria.** <How we know we can move on.>

## Risks & open questions

- <Risk>: <mitigation>

## Invariants

- <The non-negotiables, restated for an executor with less context than
  the planner: gate green at every phase boundary; never weaken a test,
  tolerance, or assertion; authority order development/architecture.md > spec.md >
  plan.md > tasks.md; decisions beyond your authority are escalated in
  report.md using the exact marker token defined in development/adr/README.md
  ("DECISION-PENDING" immediately followed by a colon), never resolved
  locally. Do not write the live marker itself here — plan text is not a
  report, and a stray marker would trip the reviewer's register check.>

## Review checklist

- <Feature-specific checks for the Reviewer: the claims most worth
  re-verifying, the plausible regressions, the criteria easiest to fake.>
