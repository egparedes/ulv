---
name: reviewer-playbook
description: |
  How the Reviewer judges a phase. Use when reviewing a diff, auditing
  an implementation, deciding GO vs NEEDS-WORK, or when asked "is this
  good", "review this", "find problems". Method: verify claims yourself,
  read as the future maintainer, hunt what's absent as hard as what's
  present, and propose alternatives with every finding. Companion to the
  reviewer subagent and the /verify command.
---

# Reviewer playbook

Complexity is incremental (PoSD): a hundred locally fine changes can
still rot a system, so the review judges the design trajectory, not just
the diff. Independence is the value — your evidence comes from the repo
and the gate, never from the Developer's narrative.

Shared ground rules: `.agents/skills/design-principles/SKILL.md`.

## Method

1. **Read as the future maintainer first.** Before any checklist, read
   the diff cold: everything you had to puzzle out — a name, a control
   flow, an implicit invariant — is a finding (nonobvious code), even
   when the code is correct (PoSD).
2. **Assume competence, then check.** When something looks wrong, ask
   "what led them to do this?" — the answer is either a constraint
   worth recording or a confirmed defect. Both are findings (Brooks).
3. **Run the red-flag checklist** from
   `.agents/skills/design-principles/SKILL.md`
   over the diff: shallow modules, information leaks, pass-throughs,
   repetition, vague names, anemic domain objects, rules buried in
   conditionals, comments that restate code, train wrecks, coincidence.
4. **Probe the change amplification.** Pick two plausible future
   changes in this area and count the places each would touch after
   this diff. A rising count is a design defect with all tests green
   (PoSD).
5. **Hunt what's absent.** Missing error-path handling, missing tests
   for states the plan names, missing assertion for a stated invariant,
   missing doc/glossary update for changed vocabulary, missing
   escalation for a visible deviation. Absence is where defects hide
   from diff-reading.
6. **Interrogate the tests, not just the code.** Do they test the
   contract or mirror the implementation? Would they catch three
   plausible bugs you can name (saboteur thinking)? Is state space
   covered or only the happy line? A vacuous test is worse than a
   missing one (PP).
7. **Check the language.** New names against `development/glossary.md`
   and the spec's Glossary; vocabulary drift between code and domain is
   a real defect — it compounds (DDD).
8. **Every finding proposes a way out.** Cite `path:LINE`, state the
   concrete failure or cost, and give the smallest fix — plus a design
   alternative when the defect is structural. Options, not lame
   objections (PP). Discard what you can't substantiate; "might be an
   issue" is not a finding.
9. **Close with the trajectory verdict.** One paragraph: did this
   change make the next change easier or harder, and why. This is the
   sentence maintainers will thank you for.

## Gotchas

- Findings still rank MAJOR / MINOR / INFO and the gate contract stays
  as `.agents/subagents/reviewer.md` defines it — this playbook adds
  review depth, it does not soften or replace the verdict rules.
- Design findings on code the diff merely touches (not introduces) are
  INFO follow-ups, not blockers — the red-flag zero-tolerance applies
  to *new* complexity.
- Don't pad the verdict with praise; the absence of findings is the
  praise. A practice worth repeating goes in the trajectory paragraph
  as *evidence for the verdict*, not as a compliment section.
