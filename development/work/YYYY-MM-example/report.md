# Report

> Written by the Developer as the work happens (deviations and dead ends are
> recorded when they occur, not reconstructed later), completed before the
> final `/verify`, and audited for honesty by the Reviewer. Frozen once the
> feature merges: never retro-edit a merged report — new findings go in the
> report of the feature that finds them.

## What was built

<What actually shipped, versus what spec.md promised. A few sentences.>

## Deviations from plan

<Every deviation, declared: what changed and why. "None" is a valid entry.
An undeclared deviation found by the Reviewer is a defect.>

## What didn't work

<Approaches tried and abandoned, with the evidence that killed them — so the
next agent doesn't re-litigate them blind. "Nothing abandoned" is valid.>

## Decisions escalated

<One line per decision that exceeded the agent's authority, each starting
with the marker token — "DECISION-PENDING" immediately followed by a colon
— and the decision needed. (Spelled out rather than written literally: a
live marker in this scaffold would have no register row, which is exactly
what the Reviewer's register check flags as a defect.) Each line gets a row
in the decision register (development/adr/README.md) in the same PR. "None"
is a valid entry.>

## Follow-ups

<Deferred work, discovered debt, ideas explicitly left out of scope.>

## Gate

<Final verification-gate result, with the date it was run.>
