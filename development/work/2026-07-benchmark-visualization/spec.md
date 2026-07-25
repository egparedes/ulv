# Unladen Velocity — Static Benchmark Visualization Generator

## Problem

Teams that track performance benchmarks over time have their results locked
into the tool that produced them. ASV's rich browsable dashboard (history
graphs, machine/parameter comparisons) is only reachable through ASV's own
benchmark-running workflow, and Bencher results are only fully explorable
through Bencher's hosted, dynamic service. A team that already has result
data — from either tool — and just wants to publish an inspectable dashboard
on a plain static host (e.g. GitHub Pages) has no standalone way to do it.
They either adopt an entire benchmarking framework they don't need or run a
dynamic backend they don't want.

## Goal

A CLI tool that reads existing benchmark result data (native ASV results, or
Bencher data from local files or fetched from a Bencher server) and generates
a self-contained static HTML site for visualizing and inspecting those
benchmarks, servable by any plain HTTP server.

## Users & stakeholders

- **Project maintainers** who publish performance dashboards for their
  projects and need them hostable on static infrastructure at zero
  operational cost.
- **Contributors and performance engineers** who browse the generated site
  to inspect benchmark histories and compare machines/configurations.
- **CI pipelines** that invoke the tool non-interactively after benchmark
  runs to regenerate and deploy the site.
- **Future plugin authors** who will add new input formats or output
  generators; they are affected by, but do not sign off on, this spec.
- **Sign-off:** the project owner (repository owner).

## Success criteria

- Given a directory of native ASV result data (machine descriptions,
  benchmark metadata, per-commit result files), one CLI invocation produces
  an output directory of only static assets — verified by serving it with a
  plain static file server and browsing it with no errors.
- The generated site shows, for each benchmark, a history graph of measured
  values across commits/revisions, and the plotted values match the values
  present in the input data for spot-checked benchmarks.
- For parameterized ASV benchmarks and results from multiple machines, the
  site lets the viewer filter/select by machine and by benchmark parameters,
  and each selection shows only the matching series.
- Native ASV input produces a correct site from result files alone, with no
  git repository present; when the project's git repository is available,
  the same invocation additionally reflects repository-derived enrichment
  (commit ordering, dates, commit links) — both cases verified on the same
  result set with and without the repository.
- Given multiple Bencher Metric Format JSON files (benchmark name → measure
  → value with optional lower/upper values) plus explicit per-file metadata
  (commit/date/branch supplied via filename convention, manifest, or CLI
  flags), one CLI invocation produces a site whose history graphs order
  points according to that metadata — verified by supplying files in
  shuffled order and checking the series order follows the metadata, not
  file order or timestamps.
- Given a single lone BMF snapshot, the CLI produces a browsable
  non-time-series view (table/bar presentation) of its benchmarks and
  measures, showing lower/upper bounds when present.
- Given a Bencher server, project identifier, and API token, one CLI
  invocation fetches results over the Bencher REST API and produces the same
  kind of static site as from equivalent local files — verified against a
  stubbed/recorded API endpoint.
- Given Bencher data spanning multiple testbeds plus a user-provided
  decomposition (a mapping or rules that translate each testbed name into
  values of declared independent factors such as OS version,
  platform/architecture, dependency version, RAM), the generated site lets
  the viewer filter/compare by each declared factor independently —
  verified by selecting one factor value and checking that only the series
  from matching testbeds are shown.
- Given the same multi-testbed Bencher data with no decomposition provided,
  the tool still generates a working site in which the testbed appears as a
  single opaque filter axis — verified by browsing and filtering by testbed
  name.
- A testbed name not covered by the user-provided decomposition fails
  generation by default: non-zero exit, the uncovered testbed named in the
  diagnostic, no site emitted — verified by supplying a mapping that omits
  one testbed. With an explicit opt-in flag/config key, the same input
  instead produces a site that includes the uncovered testbed with
  undefined/"unknown" factor values, and the diagnostic still names it —
  verified by re-running with the flag. It is never silently mis-parsed or
  dropped.
- The generated site works when hosted under a non-root URL path (e.g. a
  GitHub Pages project page) — verified by serving it from a subdirectory
  and browsing it with no broken assets or links.
- The generated site performs no network requests other than fetching its
  own static files — verified by inspecting requests while browsing.
- The CLI reads its settings from a config file (TOML or JSON), and any
  setting can be overridden by a CLI flag — verified by setting a value both
  ways and confirming the flag wins.
- The CLI provides a local preview command that serves the generated site
  for inspection in a browser — verified by running it and loading the site.
- Invoking the CLI on malformed or unrecognized input exits with a non-zero
  status and a message identifying the offending input; it never emits a
  partially broken site for that input.
- A new input format or a new output generator can be added without
  modifying the shipped ones — verified by registering a minimal dummy
  plugin of each kind in a test and exercising it end to end.
- The CLI provides `--help` output that documents every command and option —
  verified by running it and checking each documented invocation works.

## Non-goals

- **Defining or running benchmarks.** No benchmark discovery, environment
  management, repository checkout/build, scheduling, or result collection —
  the tool consumes results others produced.
- **Regression detection (v1).** No step detection, regression listings, or
  alerting; v1 ships graphs and inspection views only. Future work.
- **Any dynamic or server-side behavior in the generated site.** No
  authentication, no live updating, no database; the only bundled server is
  the local preview command, which is a development convenience, not part of
  the published output.
- **Replicating Bencher's hosted service.** No threshold/alert management,
  PR comments, user accounts, or acting as a Bencher API server; the Bencher
  API is consumed read-only to fetch results.
- **Combining input formats in one site (v1).** Each generated site is built
  from a single input format; merging ASV and Bencher data into one site is
  out of scope.
- **Inferring BMF history ordering.** No guessing from file modification
  times or lexicographic filenames; ordering requires explicit metadata.
- **Automatic testbed decomposition.** No heuristic parsing of testbed names
  into environment factors; decomposition happens only when the user
  supplies it.
- **Output formats other than static HTML** (the architecture must allow
  them later, but none ship now).
- **Modifying or writing back result data.** Inputs are read-only.
- **Format conversion as a product feature.** The tool visualizes; it is not
  an ASV↔Bencher data converter.
- **Historical ASV data migration tooling** beyond reading whatever result
  data the user already has.

## Decisions

1. **Bencher REST API is in scope for v1.** The tool can fetch results
   directly from a Bencher server (given project and token), in addition to
   reading local BMF and API-export JSON files.
2. **Reuse ASV's existing web UI for v1.** The browsing experience is the
   one extracted from ASV; the pluggable output-generator architecture must
   keep the door open for a rebuilt/modern frontend as an alternative
   generator later.
3. **BMF time axis comes from explicit sidecar metadata only** (per-file
   commit/date/branch via filename convention, manifest, or CLI flags) — no
   mtime or lexicographic guessing. A single lone BMF snapshot is supported
   and rendered as a non-time-series view (table/bar), not a history graph.
4. **Git access is optional enrichment.** The tool must work from result
   files alone; when a repository is available it may enrich commit
   ordering, dates, and URLs.
5. **One input format per generated site in v1.** No combining ASV and
   Bencher sources into a single site.
6. **No regression detection in v1.** Graphs and inspection views only;
   detection is explicit future work.
7. **CLI UX:** config file (TOML/JSON) with CLI flag overrides, plus a local
   `serve`/preview command in v1.
8. **Testbed decomposition is user-provided, never inferred.** Bencher's
   single flat testbed axis can be decomposed into independent environment
   factors (e.g. OS version, platform/architecture, dependency version, RAM,
   other hardware specs) so the site can filter/compare along each factor
   independently, analogous to ASV's machine and benchmark-parameter axes —
   but only via decomposition information the user supplies (e.g. in
   config: splitting rules or an explicit testbed → factor-values mapping).
   Without it, testbed remains a single opaque axis; testbed names not
   covered by the decomposition are reported, never guessed. The concrete
   decomposition mechanism (rule syntax, mapping format) is left to the
   architecture plan.
9. **Uncovered testbeds fail generation by default.** When a decomposition
   is supplied, a testbed name it does not cover is an error (non-zero exit,
   named in the message, no site emitted). An explicit opt-in flag/config
   key (e.g. `--allow-unmapped`) instead includes such testbeds with
   undefined/"unknown" factor values so the site still builds. Either way
   the uncovered names are reported, never silently mis-parsed or dropped.
