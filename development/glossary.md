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

Seeded once from [`architecture.md`](architecture.md) and `ulv.model` when the
harness adopted this register ([ADR 0010](adr/0010-development-tree-and-process-memory.md)),
because the vocabulary predates the register. Everything after that arrives
through the channel described above.

### The data model

- **Dataset** — the whole benchmark corpus a single build renders: its
  revisions, environments, benchmarks, and result series, validated for
  referential integrity. Frozen once loaded, so every consumer can share
  one instance. (code: `Dataset`)
- **Revision** — one point on the history axis, typically a commit. Carries
  the commit hash, date, tags, and the branches containing it. (code:
  `Revision`)
- **Environment** — where results were produced, described as independent
  factors rather than a single opaque label. (code: `Environment`)
- **Factor** — one filter axis of an environment: machine, python, a
  requirement version, an env var, or a factor decomposed from a testbed.
  Four names are reserved by the pipeline (`machine`, `branch`, `testbed`,
  `summary`).
- **Benchmark** — a measured quantity, optionally parameterized over one or
  more parameter axes. (code: `Benchmark`)
- **Result series** — the measurements for one (benchmark, environment) pair
  across revisions. (code: `ResultSeries`)
- **Result point** — one measurement: a scalar, or one value per parameter
  combination for a parameterized benchmark. `None` means the run failed or
  is missing — never zero. (code: `ResultPoint`)
- **Testbed** — Bencher's flat "where it ran" axis. Decomposed into factors
  only through an explicit `[testbeds]` config table, never by parsing the
  name.
- **Snapshot** — how a dataset with a single revision renders: a table
  rather than graphs, because there is no time axis to plot. (code:
  `Dataset.has_time_axis`)

### The pipeline

- **Input format** — a plugin that reads some external source and returns a
  `Dataset`. Built-ins: `asv`, `bmf`, `bencher-api`. (code: `InputFormat`)
- **Output generator** — a plugin that turns a `Dataset` into a static site.
  Built-ins: `html` (vendored ASV frontend) and `html-uplot` (self-authored
  uPlot frontend). (code: `OutputGenerator`)
- **Enrichment** — optional metadata pulled from a git repository
  (topological order, committer dates, tags, branch membership) to improve a
  dataset an input format already built.
- **Graph** — one plotted series as the frontend fetches it: a JSON file
  whose on-disk path is derived from the environment's factors and the
  benchmark name.
- **Graph paths manifest** — the `graph_paths` key in `index.json`, which
  publishes every sanitized graph path so a frontend never recomputes them
  client-side.
- **Atomic output** — the build discipline: sites are written to a hidden
  sibling directory and swapped in only on success, so a failed build never
  leaves a half-written site.
