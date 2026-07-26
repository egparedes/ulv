# 2. Plugin discovery via importlib.metadata entry points

## Status

Accepted

## Context

The spec requires that a new input format or output generator can be
added without modifying the shipped ones, verified by registering a
minimal dummy plugin of each kind in a test and exercising it end to
end. We need a discovery mechanism for third-party plugins that:

- adds zero runtime dependencies (the project ships with none);
- works for plugins distributed as separate installed packages;
- also works in-process, so tests (and embedders) can register a
  plugin without building and installing a distribution;
- cannot let a third-party package break or shadow the built-in
  formats.

Candidates considered: `importlib.metadata` entry points (stdlib),
`pluggy` (adds a dependency and a hook-call model we don't need for
two small protocols), and namespace-package scanning (import-time side
effects, no explicit registration record).

## Decision

Use two `importlib.metadata` entry-point groups, one per plugin kind:

- `ulv.input_formats` → objects satisfying the `InputFormat` protocol
  (`name`, `load(source, options) -> Dataset`);
- `ulv.output_generators` → objects satisfying the `OutputGenerator`
  protocol (`name`, `generate(dataset, out_dir, options)`).

An entry point may reference either a plugin class (instantiated with
no arguments) or a ready instance. Each group is backed by a
`Registry` in `ulv.plugins` exposing `register()` / `get()` /
`names()`; built-ins are registered programmatically at import, and
tests use the same `register()` API for dummy plugins.

Discovery is lazy (first `get()`/`names()` call) and explicit
registrations always win: an entry point whose name is already
registered is skipped, so built-ins cannot be shadowed. Unknown plugin
names raise `UlvError` listing the available names.

## Consequences

- Third parties ship plugins as ordinary packages with an
  `[project.entry-points."ulv.input_formats"]` (or output group) table;
  no ulv code changes needed.
- Tests exercise the extensibility criterion with in-process
  `register()` calls plus a monkeypatched `entry_points()`; no
  package-building fixture required.
- Entry-point loading executes third-party code at first lookup; a
  plugin that raises on import fails the run at that point. Acceptable:
  the failure is attributable in the traceback, and lazy discovery
  keeps `--help`-style invocations unaffected.
- Two registries instead of one keeps the two protocols from sharing a
  namespace; a name like `html` can exist in both groups.
