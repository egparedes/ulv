## Feature

<!-- Link the development/work/<YYYY-MM>-<slug>/ directory this PR delivers, or state
     that the change was small enough to skip the four-phase loop. -->

## Definition of done

- [ ] Gate green: `make verify` run locally, exit 0
- [ ] Every success criterion in `spec.md` has observable evidence
      (a passing test, a screenshot, a log line)
- [ ] `report.md` written: what was built, deviations declared, negative
      results recorded, follow-ups listed
- [ ] No test, tolerance, or assertion weakened to make the gate pass;
      any new skip is explained in `report.md`
- [ ] Every `DECISION-PENDING:` line added by this PR has a row in the
      decision register (`development/adr/README.md`)
- [ ] New structural decisions (dependency, persistence, protocol, auth)
      have an ADR in `development/adr/`

## Deviations & notes for the reviewer

<!-- Anything the diff doesn't say: tolerances touched? interfaces changed?
     surprises worth a second look? -->
