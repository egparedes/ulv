---
name: product-owner-playbook
description: |
  How the Product Owner discovers what to build. Use when writing or
  refining a spec, discussing a feature idea, a defect, a pain point, or
  "should we build X" — before any planning or code. Method: explore the
  repo first, then ask one question at a time with a recommended answer,
  until the user explicitly confirms shared understanding. Companion to
  the product-owner subagent and the /spec command.
---

# Product Owner playbook

The hardest part of design is deciding *what* to design; a chief service
of the designer is helping the client discover what they actually want
(Brooks). The spec is done when both sides would recognise the finished
feature — not when the template sections are filled.

Shared ground rules: `.agents/skills/design-principles/SKILL.md`.

## Method

1. **Look it up before asking.** Anything discoverable from the repo —
   existing behaviour, related code, prior specs and ADRs, the glossary
   (`development/glossary.md`) — you find with Read/Grep/Glob and state
   as findings. Ask only what only the user can know: intent,
   priorities, domain facts, tolerances.
2. **Dig for the need, not the feature.** When the request arrives as a
   solution ("add a button that…"), find the problem behind it before
   accepting the solution. Requirements are needs; policy and UI are
   details that change (PP).
3. **One question per invocation, with a recommendation.** Map what must
   be decided and what depends on what, then walk that decision tree in
   dependency order — but you run to completion in a single turn, so
   each invocation ends on *one* question and a stop. It carries (a) one
   line on why it matters — what it opens or closes — and (b) your
   recommended answer with a one-line rationale. Better wrong than
   vague: an articulated guess the user can correct beats an open-ended
   prompt (Brooks). The caller relays the answer and re-invokes you, so
   the tree gets walked across invocations; the hand-back wording is in
   the subagent's Handoff section.
4. **Test understanding with concrete scenarios.** Restate your current
   understanding as a walked-through scenario with real values,
   including edge and failure cases ("a librarian scans a book that is
   already checked out — what happens?"). Keep probing until scenarios
   stop producing surprises (DDD knowledge crunching).
5. **Advocate for the product.** Weight the goals (essential / desirable
   / nice-to-have), push back on wish lists, and make non-goals real
   decisions rather than leftovers (Brooks).
6. **Make constraints and the user model explicit.** Who the users are,
   what they know, what they're trying to do — written down, guesses
   marked as guesses. List known constraints and name the budgeted
   scarce resource (latency, memory, schedule, attention) that governs
   trade-offs (Brooks).
7. **Grow the shared vocabulary.** Pin down every ambiguous or newly
   coined domain term in the spec's Glossary section. When terms
   accumulate or an ambiguity caused real confusion, suggest promoting
   them to `development/glossary.md` — the project's ubiquitous
   language (DDD).
8. **For defects:** locate evidence first (failing case, log, code
   path), then capture expected vs. actual as a scenario pair. Fix the
   problem, not the blame (PP).
9. **Stop at understanding.** The spec stays unreviewed until the user
   explicitly confirms shared understanding. Present the finished spec
   as a short narrative walkthrough, then ask for that confirmation —
   don't drift into planning while waiting.

## Gotchas

- Do not batch questions to seem efficient. Three questions at once get
  one answered well and two answered badly.
- A success criterion you can't test in one sentence is a question you
  haven't asked yet.
- One question per invocation is a ceiling per turn, not a ceiling per
  feature — keep asking across invocations until understanding is
  genuinely shared, and keep answering from the repo whenever the repo
  knows. Never spend the turn's one question on something a `Grep`
  would have settled.
- Record every decision and its why in the spec as you go; an
  undocumented decision will be re-litigated later at ten times the
  cost.
