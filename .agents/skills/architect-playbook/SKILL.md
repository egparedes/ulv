---
name: architect-playbook
description: |
  How the Architect turns an approved spec into a plan. Use when writing
  or revising plan.md, choosing a design, weighing alternatives, or when
  a spec assumption needs a prototype/spike before committing. Method:
  design it twice, spike the risky assumptions, make phase 1 a tracer
  bullet, specify deep modules with an error strategy. Companion to the
  architect subagent and the /plan command.
---

# Architect playbook

The plan is written for an executor with less context than you: fresh
session, weaker model, no access to this conversation. It must carry not
just the design but the *whys* — rationale that isn't recorded will be
re-argued or silently violated later (Brooks).

Shared ground rules: `.agents/skills/design-principles/SKILL.md`.

## Method

1. **Study exemplars first.** Grep for precedents — modules, idioms,
   prior features of the same shape — and match them unless you record a
   reason not to. Originality is no excuse for ignorance (Brooks);
   consistency is leverage (PoSD).
2. **Design it twice.** Sketch at least two genuinely different
   decompositions before choosing. Compare on: interface simplicity for
   callers, information hiding, blast radius of likely changes,
   cognitive load — and on the budgeted resource the spec's
   **Constraints** section names, which is the axis the trade-off is
   actually being made against. Record the loser and why it lost in the
   plan's Architecture decisions block — a decision with no recorded
   alternative is a habit, not a decision (PoSD).
3. **Spike before you commit.** List the spec's and design's assumptions
   and rank by (impact if wrong × uncertainty). For risky-but-cheap
   ones, request a spike: a disposable experiment answering ONE question
   (does the API paginate? is the parser fast enough?). You cannot run
   code yourself — hand back to the main agent using the protocol in the
   architect subagent's Handoff section, and fold the returned findings
   into the plan. Spike code is never promoted: the value is the lesson,
   not the code (PP: prototype to learn).
4. **Phase 1 is a tracer bullet.** When the feature spans layers, make
   the first phase the thinnest end-to-end slice through the real
   architecture, kept for keeps — then every later phase mutates a
   complete, working system instead of assembling parts that have never
   met (PP; Brooks: progressive truthfulness).
5. **Specify deep modules.** For each new or reshaped module: purpose,
   interface sketch, the *secrets* it hides, and what it must not
   expose. Minimal implementation, slightly general interface. Reject
   your own design if an interface is nearly as complex as what it
   hides (PoSD).
6. **Design the error strategy, don't inherit it.** Per boundary: which
   failure cases are defined out of existence by API shape, what
   crashes early, what is handled — and where. "Wrap it in try/catch"
   is not a strategy (PoSD; PP).
7. **Name in the ubiquitous language.** Take names from
   `development/glossary.md` and the spec's Glossary section; if the
   design needs a concept the glossary lacks, that's a finding for the
   spec, not a private invention (DDD).
8. **Tests are part of the design.** Phase tests state *which contract*
   and *which states* they prove — if a phase is hard to test, change
   the design, not the test's honesty (PP).
9. **Flag the irreversible.** Storage formats, public APIs, wire
   protocols, dependencies: mark each hard-to-reverse choice, prefer
   the reversible variant when nearly equal, and surface the rest for
   explicit confirmation (or an ADR — check the bar in
   `development/adr/README.md`).

## Gotchas

- Spike findings that contradict the spec go back to the Product Owner
  as spec feedback — don't quietly plan around a broken assumption.
- Smallest-design pressure applies to implementation scope, not to
  skipping the second design sketch; the comparison is cheap and it is
  where most design errors die.
- Don't spread one concern across phases so each phase looks small;
  phases slice by abstraction delivered, not by file count.
- The Invariants block exists because plans outlive conversations —
  restate the non-negotiables even when they feel obvious to you now.
