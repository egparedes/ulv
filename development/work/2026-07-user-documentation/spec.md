# User Documentation

## Problem

Unladen Velocity (ulv) users currently have no guided documentation showing
how to use the tool in practice. The README is developer-focused (make
commands, agent conventions), and the architecture docs describe internal
structure rather than end-user workflows. A new user wanting to visualize
benchmark data must reverse-engineer CLI options from `--help` output, read
source code to understand input format requirements, and experiment to
discover working invocations. This learning curve delays adoption and
increases support burden.

Additionally, the existing hand-written CLI reference (`docs/user/cli-reference.md`)
risks drifting from the source code as the CLI evolves. Keeping documentation
in sync manually is error-prone and adds maintenance burden.

## Goal

Users can follow worked examples in `/docs/user/` to generate and view
benchmark visualizations from ASV results, Bencher Metric Format files, or
Bencher cloud data without consulting source code. CLI and API reference
documentation stays accurate automatically because it is generated from source.

## Users & stakeholders

- **Primary users:** Developers with benchmark data who want to visualize
  trends over time using ulv.
- **Secondary users:** CI/CD engineers integrating ulv into automated
  pipelines.
- **Stakeholders:** Maintainers responsible for user support and documentation
  accuracy.

## Success criteria

### Content requirements

1. **Quickstart example runs end-to-end.** A user can clone the repo, run
   the documented quickstart command against included sample data, and open
   the resulting HTML site in a browser.

2. **Each input format has a runnable example.** The documentation includes
   at least one complete `ulv build` invocation for each supported input
   format (asv, bmf, bencher-api), using either bundled sample datasets or
   documented external sources.

3. **Common options are demonstrated.** Examples show how to set project
   name, enable git enrichment with branches and tags, configure commit
   links, and decompose testbeds into factors.

4. **Bencher cloud integration is documented.** A dedicated section shows
   how to fetch data from a Bencher server, including authentication via
   environment variable and project selection.

5. **Sample datasets are provided when needed.** If runnable examples require
   sample data not already present in the repo, that data is added under a
   documented location (e.g., `docs/user/samples/` or repurposed test
   fixtures).

6. **Preview workflow is documented.** The `ulv serve` command is explained
   as a local preview mechanism, with an example invocation.

7. **Config file usage is documented.** At least one example shows
   `ulv.toml` configuration as an alternative to CLI flags.

### Documentation generation

8. **Zensical generates the documentation site.** The user documentation is
   built using Zensical (https://zensical.org). Running the documentation
   build produces a navigable HTML site from the source markdown and
   generated reference pages.

9. **CLI reference is auto-generated from source.** The CLI reference
   (commands, subcommands, options, types, defaults, help text) is extracted
   automatically from the argparse definitions in `src/ulv/cli.py`. Adding
   or changing a CLI option in source code updates the reference without
   manual edits.

10. **API reference is auto-generated from source.** Public module docstrings
    and type hints from `src/ulv/` are rendered into API reference pages.
    The reference covers the data model (`model.py`), configuration
    (`config.py`), and any other modules intended for programmatic use.

11. **Generated reference stays current.** A test or CI check fails if the
    generated documentation is stale relative to the source code, ensuring
    drift is caught before merge.

### Build integration

12. **Makefile task builds documentation.** A `make docs` target (or similar)
    generates the full documentation site, following the repo's existing
    Makefile conventions (`uv run` prefix, help comment, `.PHONY` declaration).

13. **Makefile task serves documentation locally.** A `make docs-serve` target
    (or similar) starts a local preview server for the generated documentation.

14. **Documentation build integrates with verify.** Either `make verify`
    includes documentation generation checks, or a separate `make docs-check`
    target validates that generated files are up to date.

15. **Zensical is a dev dependency.** Zensical is added to the `dev`
    dependency group in `pyproject.toml` so contributors can build docs
    without additional setup beyond `uv sync`.

## Non-goals

- **Plugin development guide.** Documenting how to write custom input or
  output plugins is out of scope; the plugin protocol is internal API.

- **Contributor/developer documentation.** Docs on testing, style, ADRs,
  and CI remain under `/docs/` and are not part of the generated user
  documentation site.

- **Tutorial video or interactive walkthrough.** Text-based documentation
  only.

- **Regression detection documentation.** The step-detection feature is
  explicitly deferred (spec Decision 6); documenting placeholders or
  null behaviors is out of scope.

- **Hosted documentation deployment.** This spec covers local generation
  and preview; CI/CD deployment to a hosted site (GitHub Pages, etc.) is
  out of scope.

- **Full API coverage.** Only public-facing modules with stable interfaces
  are documented; internal modules, private functions, and plugin internals
  are excluded from the API reference.

## Open questions

1. **Sample data placement.** Should user-documentation examples reuse
   existing test fixtures (e.g., `tests/fixtures/asv_results/`), or should
   a separate `docs/user/samples/` directory contain purpose-built minimal
   examples? Reuse reduces duplication; dedicated samples can be more
   pedagogically clear.

2. **Bencher cloud example project.** The bencher-api examples need a
   publicly accessible project on the Bencher cloud instance. Is there a
   known public project to reference, or should examples use a placeholder
   project slug with instructions for users to substitute their own?

3. **Zensical configuration.** The Architect should verify Zensical's
   configuration format (zensical.toml, zensical.yaml, or pyproject.toml
   section) and determine how to wire argparse introspection and docstring
   extraction into the build. See https://zensical.org/docs/ for details.

4. **Existing CLI reference migration.** The current hand-written
   `docs/user/cli-reference.md` contains accurate content. Should it be
   replaced entirely by generated output, or should generated content be
   merged into the existing structure (e.g., generated tables with
   hand-written prose sections)?
