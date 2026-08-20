# 6. Zensical documentation generator

## Status

Accepted

## Context

User documentation lives in markdown under `docs/user/`, but users need
a polished, navigable HTML site they can read without cloning the repo.
The spec mandates generated CLI and API references that stay in sync
with source automatically, catching drift before merge. Alternatives
considered:

- MkDocs: mature, plugin-rich, but slow builds and Python 2-era APIs.
- Sphinx: powerful for large projects, heavyweight for our scope.
- Hugo/mdBook: cross-language, requires managing a separate toolchain.
- Hand-written HTML: no staleness checks, maintenance burden.

Zensical is a modern static site generator that supports MkDocs-style
configuration (including mkdocstrings for API references) with faster
builds. It produces a Material-styled site from markdown with minimal
configuration.

## Decision

- Add `zensical>=0.0.47` to the `dev` dependency group.
- Configuration lives in `zensical.toml` at the repo root.
- Source directory: `docs/user/`; output directory: `_site/` (gitignored).
- CLI reference is auto-generated from argparse via a custom script that
  introspects the parser and emits markdown; Zensical renders it.
- API reference uses mkdocstrings (optional dependency) to document
  public modules: `model`, `config`, `errors`, `testbeds`, `plugins`.
- Makefile targets: `make docs` (build), `make docs-serve` (preview),
  `make docs-check` (staleness verification integrated into verify.sh).

## Consequences

- Contributors can build docs with `uv sync && make docs` — no separate
  toolchain.
- CLI and API changes surface as doc drift in `make verify`, preventing
  stale documentation from merging.
- Zensical is a dev-only dependency; the runtime remains zero-dependency.
- mkdocstrings is added as an optional dev dependency for API docs.
