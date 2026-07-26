---
name: design-principles
description: |
  The project's software-design ground rules and red-flag checklist. Use
  whenever designing, planning, implementing, refactoring, or reviewing
  code — any time you choose module boundaries, name things, handle
  errors, or judge whether a change is "good enough". The role playbooks
  (product-owner, architect, developer, reviewer) build on this file;
  it is the shared core they all cite.
---

# Design principles

Distilled from four sources: Ousterhout, *A Philosophy of Software Design*
(PoSD); Hunt & Thomas, *The Pragmatic Programmer* (PP); Evans,
*Domain-Driven Design* (DDD); Brooks, *The Design of Design* (DoD).
Tags in parentheses give provenance, not further reading assignments.

## Prime directives

1. **Complexity is the enemy, and it is incremental.** No "too small to
   matter"; fix broken windows when you touch them (PoSD; PP).
2. **Working code isn't enough.** Invest continually in design, don't
   just take the fastest diff that passes (PoSD).
3. **The domain is the heart of the software.** Model it in the domain's
   own language and keep model and code bound together (DDD).
4. **Design is iterative discovery.** Goals, requirements, and
   constraints are found while designing, not given up front (DoD).
5. **DRY.** Every piece of knowledge — code, schema, doc, config — has
   one authoritative representation (PP).
6. **Design for reading, not writing.** The future reader outranks the
   present writer (PoSD).
7. **You can't write perfect software — be paranoid.** Contracts,
   assertions, crash early: a dead program does less damage than a
   crippled one (PP).
8. **There are no final decisions.** Keep choices reversible;
   abstractions outlive details (PP).

## Modules and interfaces

- Make modules **deep**: simple interface over powerful implementation.
  The interface is the cost; a simple interface matters more than a
  simple implementation (PoSD).
- **Hide information.** A design decision reflected in more than one
  module is a leak. Decompose by knowledge, never by execution order
  (PoSD).
- Implement what's needed now, but shape the **interface** for the class
  of needs — somewhat general-purpose, not special-cased to today's
  caller (PoSD).
- **Different layer, different abstraction.** Pass-through methods and
  thin wrappers signal a wrong decomposition (PoSD).
- **Pull complexity downward.** Better the module author suffers than
  every caller; don't export your problem as a config parameter (PoSD).
- **Eliminate effects between unrelated things.** Shy code, Law of
  Demeter; one requirement change should land in one module (PP).
- **Define errors out of existence.** Redesign the API so the
  exceptional case is normal semantics where possible; handle the rest
  in as few places as possible; exceptions only for the exceptional
  (PoSD; PP).
- **Policy in metadata, mechanism in code**; views separate from models
  (PP).

## Domain and naming

- Name every code element with the exact terms the domain experts use
  (see `development/glossary.md`); a vocabulary change is a rename, in
  the same change (DDD).
- Business rules are **named concepts**, not buried conditionals; when
  experts use a word the code doesn't have, reify it (DDD).
- Domain objects carry their behaviour — don't drain logic into service
  code and leave anemic data bags (DDD).
- Precise, consistent names; if a precise name is hard to find, the
  design — not the vocabulary — is unclear (PoSD).

## Construction

- **Comments say what the code can't**: why, invariants, units,
  ownership. Interface comments never describe implementation. A comment
  that repeats the code is noise (PoSD).
- **Design by contract**: preconditions, postconditions, invariants as
  assertions that stay on; crash early rather than limp; the allocator
  of a resource frees it (PP).
- **Never program by coincidence.** Rely only on documented behaviour;
  prove assumptions with real data; understand generated code before
  committing it (PP).
- **Test the contract, cover the states** — not the lines. Every bug
  found gets a regression test before it gets a fix (PP).
- **Refactor on its own commits**, never mixed with behaviour change
  (PP; PoSD).

## Red-flag checklist

Stop and reconsider when you see one of these:

- Shallow module — interface barely simpler than its implementation.
- Information leak — one decision visible in several modules.
- Pass-through method — same signature relayed one level down.
- Temporal decomposition — structure mirrors execution order.
- Nontrivial repetition — knowledge represented twice.
- Special-purpose code tangled with general-purpose code.
- Vague or hard-to-pick name; entity that's hard to describe briefly.
- Comment that repeats the code; implementation detail in an interface
  comment.
- Train wreck — `a.getB().getC().doD()`.
- Coincidental correctness — it works but nobody can say why.
- Anemic domain object; business rule living only in a conditional;
  code vocabulary drifting from the experts' speech.
- Manual procedure a script should own.
- Broken window left standing.

## Gotchas

- "Smallest design that satisfies the spec" (the Architect's rule) and
  "somewhat general-purpose" do not conflict: minimal *implementation*,
  slightly general *interface*.
- Zero tolerance for red flags means *name and rank them*, not
  "everything is a blocker" — severity still matters.
- These rules bind the *new* code you write; bringing an entire legacy
  file up to standard is its own task, not a drive-by.
