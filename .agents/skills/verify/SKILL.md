---
name: verify
description: |
  Run the project's verification gate. Use this skill whenever the user says
  "verify", "is this ready", "ready to commit", "check this", or after any
  non-trivial code change. Runs `make verify`, summarises failures with
  file:line evidence, and proposes the smallest fix that would make the next
  run pass. Never silently skips or disables a failing test.
---

# verify

## When to invoke

- After any non-trivial edit, before claiming a task is done.
- When the user signals readiness ("verify", "ready", "ship it").
- Before opening or updating a pull request.

## What to do

1. Run `make verify` in the repository root. Capture both stdout and exit code.
2. If exit code is 0 — summarise what changed since the last verify, the
   tests that ran, and stop. Do not run additional checks.
3. If exit code is non-zero — parse the output, group errors by file, and
   propose the smallest fix that would make the next run pass. Cite each
   error as `path/to/file.ext:LINE`.
4. If a test must be skipped to proceed (rare), escalate it as a
   `DECISION-PENDING:` line in the feature's `report.md` and ask the user to
   confirm (it lands as a decision-register row — or an ADR, if it clears
   the bar in `development/adr/README.md`). Never silently
   `@pytest.mark.skip`, `it.skip(...)`, or `#[ignore]` a failing test.

## Gotchas

- The `Stop` hook in `.claude/settings.json` already runs `make verify`.
  This skill is for the *interactive* case where the user wants verification
  before the agent's natural stop — and for OpenCode, which has no
  session-end gate at all.
- `verify.sh` exits with code 2 on failure (Stop-hook convention). Don't
  treat exit 2 as a different signal from exit 1 — both mean "fix it".
- On slow machines `make verify` may exceed 60s. If that becomes routine,
  raise a decision (register row) about moving slow suites to
  `make test-all` / CI.
