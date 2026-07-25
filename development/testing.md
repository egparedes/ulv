# Testing strategy

## What the agent runs

- **Pre-claim-done gate**: `make verify` (= `scripts/verify.sh`).
- **Fast loop**: `make test` — must finish in <60s. Add slow suites under
  `make test-all`.

## Reading gate output

- **Passed counts may only grow.** A drop in passed tests that the diff
  doesn't explain line-by-line (an intentional, declared removal) means:
  stop, don't commit, report the failure verbatim — the full failure block,
  not a summary.
- **Any new skip is a finding to explain,** in the feature's `report.md`,
  not to ignore.
- **Never narrow the gate to make it pass.** No `-x`, `-k`, `--ignore`
  (or your runner's equivalents), no marker edits, no deleted or weakened
  assertions. If you cannot go green within your task's scope, report
  honestly and stop.
- For large suites, consider keeping a baseline table (expected
  passed/skipped counts per command) in this file, updated in the same
  commit as any test-count change — counts are a stronger regression
  signal than timings.

## Layering

_Fill in: unit, integration, contract, e2e. Where each lives, what each
covers, when to add to which layer._

## Coverage targets

_Fill in: numeric or qualitative targets. Coverage is a smoke detector, not
a goal — don't write tests just to hit a number._

## Determinism

- Time, randomness, and I/O must be injectable.
- Snapshot tests are fine but commit the fixture, not the snapshot run output.
- Flaky tests are bugs; quarantine them in a separate target and open an issue,
  don't `@retry`.
