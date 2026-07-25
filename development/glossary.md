# Glossary — the project's ubiquitous language

One entry per domain term, as the domain experts use it. Code, specs,
plans, and conversation all use these exact terms: when a term changes
here, the corresponding code identifiers are renamed in the same change,
and when the code needs a concept this file lacks, that's a missing
entry, not a private invention.

Entry format — term, domain meaning, code name only if it must differ:

```
- **Term** — what it means in the domain, one or two sentences.
  (code: `TermInCode`, only when it can't match the term itself)
```

This file is a **register**, like the decision register in
[`adr/README.md`](adr/README.md): it accretes mid-feature through one
channel only. New terms arrive through a feature spec's **Glossary**
section (`/spec`, Product Owner): the spec proposes, the user reviews
the spec, and the reviewed entries are promoted here verbatim at
`/spec` wrap-up — the Reviewer checks each new entry against the spec
that proposed it. Renames and meaning changes are not register
traffic: those are a dedicated PR, trunk-gated like the rest of
`development/` (see [`README.md`](README.md)).

## Terms

_None yet. The first feature spec will propose some._
