# Plan

## Architecture decisions

- **Documentation location:** `docs/user/` — a new subdirectory alongside the
  existing developer-facing docs. This keeps user content discoverable without
  polluting the root or mixing with ADRs. ADR: n/a (no new dependency or
  protocol).

- **Sample data strategy:** Reuse existing test fixtures for most examples
  (`tests/fixtures/asv_results/`, `tests/fixtures/bencher_api/`); add a minimal
  dedicated BMF sample under `docs/user/samples/` for the quickstart and BMF
  walkthrough where pedagogical clarity trumps fixture reuse. ADR: n/a.

- **Bencher cloud examples:** Use placeholder slugs (`YOUR_PROJECT`,
  `YOUR_TOKEN`) with explicit substitution instructions. No live server
  dependency. ADR: n/a.

- **Verification approach:** Markdown lint via `markdownlint-cli2` (the same
  tool style.md recommends for prose) plus command-block smoke tests that run
  the documented invocations against fixtures and assert exit 0 / expected
  outputs exist. ADR: n/a (no new runtime dependency; dev/test only).

- **Documentation generator:** Zensical — the spec mandates it for building the
  user documentation site, CLI reference generation from argparse, and API
  reference from docstrings. ADR: ADR needed: zensical-documentation-generator
  (new dev dependency for documentation generation).

- **CLI reference strategy:** Replace the hand-written `docs/user/cli-reference.md`
  with auto-generated output from Zensical's argparse introspection. The current
  hand-written content is accurate but maintaining two sources of truth
  introduces drift risk. Generated output with hand-written prose sections (via
  Zensical's customization hooks) is preferred. ADR: n/a.

- **API reference scope:** Document public modules with stable interfaces only:
  `model.py` (data model), `config.py` (settings), `errors.py` (error type),
  `testbeds.py` (testbed decomposition), and `plugins.py` (plugin protocols).
  Internal modules (`cli.py` internals, `gitrepo.py`, input/output
  implementations) are excluded. ADR: n/a.

## Phase 1 — Directory scaffold and quickstart

**Scope.** Create the `docs/user/` directory structure with an index page and a
runnable quickstart example. The quickstart uses the existing ASV fixture so
users can clone the repo and immediately run `ulv build` without downloading
external data.

**Steps.**
1. Create `docs/user/index.md` with a brief intro and table of contents linking
   to subsequent pages.
2. Create `docs/user/quickstart.md` with:
   - Prerequisites (Python 3.11+, `uv`).
   - Clone repo, install with `uv sync`.
   - Run `ulv build` against `tests/fixtures/asv_results/` producing a site in
     a temp directory.
   - Open the resulting `index.html` in a browser.
   - Run `ulv serve` to preview.
3. Confirm the exact command paths work by running them manually (no automated
   test yet).

**Tests.** `make verify` passes (no new code, only markdown). A manual run of
the quickstart commands succeeds.

**Exit criteria.** A user following `docs/user/quickstart.md` can build and
preview a site using only in-repo fixtures.

## Phase 2 — ASV format guide

**Scope.** Document the `asv` input format with complete invocation examples.

**Steps.**
1. Create `docs/user/asv.md` covering:
   - Expected directory layout (`benchmarks.json`, `<machine>/machine.json`,
     `<machine>/<commit>-<env>.json`).
   - Minimal `ulv build -i asv --input-dir ... -o ...` invocation.
   - Setting project name with `--project`.
   - Git enrichment with `--repo`, `--branches`, `--show-commit-url`.
2. Use the existing test fixture path in all examples so readers can run them.

**Tests.** `make verify` passes. Example commands in the doc run successfully
against `tests/fixtures/asv_results/`.

**Exit criteria.** The ASV guide covers all spec success criteria for that
format (runnable example, common options).

## Phase 3 — BMF format guide with dedicated sample

**Scope.** Document the `bmf` input format and provide a minimal sample dataset
under `docs/user/samples/` for clarity.

**Steps.**
1. Create `docs/user/samples/bmf/` with:
   - Two or three `.json` files representing distinct commits.
   - A `manifest.json` mapping filenames to commit/date/testbed metadata.
2. Create `docs/user/bmf.md` covering:
   - Bencher Metric Format structure (`{benchmark: {measure: {value, ...}}}`).
   - Single-file invocation with `--commit`, `--date`, `--testbed`.
   - Multi-file with `--manifest` (using the new sample).
   - Multi-file with `--filename-pattern` template.
3. Link to the BMF spec (bencher.dev) for canonical schema.

**Tests.** `make verify` passes. Example commands run successfully against the
new `docs/user/samples/bmf/` directory.

**Exit criteria.** The BMF guide covers all spec success criteria for that
format.

## Phase 4 — Bencher API guide

**Scope.** Document the `bencher-api` input format for fetching data from a
Bencher server.

**Steps.**
1. Create `docs/user/bencher-api.md` covering:
   - How the input fetches reports from a Bencher server.
   - Required `--bencher-project` (or config key).
   - Optional `--bencher-url` for self-hosted instances.
   - Authentication via `BENCHER_API_TOKEN` env var (preferred) or
     `--bencher-token` flag (discouraged for shell history).
2. Use placeholder project slug (`YOUR_PROJECT`) with explicit substitution
   note.
3. Mention the transport seam exists for testing but do not document it as a
   user-facing feature.

**Tests.** `make verify` passes. No live server required; commands shown with
placeholders.

**Exit criteria.** The Bencher API guide satisfies spec success criterion 4.

## Phase 5 — Config file and testbed decomposition guide

**Scope.** Document `ulv.toml` configuration and the testbed decomposition
feature.

**Steps.**
1. Create `docs/user/config.md` covering:
   - Default config file discovery (`./ulv.toml`).
   - Explicit `--config FILE`.
   - Precedence: defaults < config file < CLI flags.
   - Full list of config keys (mirror of CLI flags, snake_case).
   - Example `ulv.toml` for an ASV project.
2. Create `docs/user/testbeds.md` covering:
   - The `[testbeds]` table with `factors` and `map`.
   - `--testbeds-file` for standalone mapping.
   - `--allow-unmapped` for lenient mode.
   - Example decomposing `linux-x64`, `macos-arm` into `os` and `arch` factors.

**Tests.** `make verify` passes. Example config files parse without error when
fed to `ulv build --config`.

**Exit criteria.** Config file usage (spec criterion 8) and testbed
decomposition are documented.

## Phase 6 — CLI reference

**Scope.** Provide a complete API reference for all CLI commands and options.

**Steps.**
1. Create `docs/user/cli-reference.md` with:
   - `ulv --version`, `ulv --help`.
   - `ulv build` with every flag, type, default, and behavior.
   - `ulv serve` with every flag.
2. Organize by subcommand, then alphabetically by flag.
3. Keep descriptions concise; link to guides for context.

**Tests.** `make verify` passes. Cross-check against `ulv build --help` and
`ulv serve --help` output to ensure nothing is missing.

**Exit criteria.** Spec success criterion 5 (API reference) is satisfied.

## Phase 7 — Verification tests for documentation

**Scope.** Add automated smoke tests that execute the documented commands and
verify they produce expected outputs.

**Steps.**
1. Create `tests/test_docs.py` with:
   - A test that runs the quickstart command against
     `tests/fixtures/asv_results/` and asserts exit 0 and `index.html` exists.
   - A test that runs the BMF sample command against `docs/user/samples/bmf/`
     and asserts exit 0.
   - A test that parses each example `ulv.toml` snippet and asserts no config
     error.
2. Optionally add a `markdownlint` step to `make verify` if not already present
   (check existing Makefile first).

**Tests.** `make verify` passes including the new `test_docs.py` tests.

**Exit criteria.** Every runnable command in the documentation is covered by at
least one automated test.

## Phase 8 — Index, cross-links, and polish

**Scope.** Finalize the documentation structure with cross-links, consistent
style, and a complete index.

**Steps.**
1. Update `docs/user/index.md` with a complete table of contents and brief
   descriptions.
2. Add navigation links (prev/next or see-also) at the bottom of each page.
3. Review all pages for consistent voice, formatting, and adherence to
   `docs/style.md`.
4. Ensure no broken internal links (relative paths).

**Tests.** `make verify` passes. Manual review confirms navigation works.

**Exit criteria.** Documentation is polished, navigable, and ready for users.

## Phase 9 — Add Zensical as dev dependency

**Scope.** Add Zensical to the dev dependency group so contributors can build
documentation without additional setup.

**Steps.**
1. Add `zensical` to the `dev` dependency group in `pyproject.toml`.
2. Run `uv sync` to verify the dependency resolves and installs.
3. Verify `uv run zensical --version` (or equivalent) works.

**Tests.** `uv sync` succeeds. `make verify` passes. The Zensical CLI is
available in the dev environment.

**Exit criteria.** Contributors can install Zensical via `uv sync` without
manual steps.

## Phase 10 — Zensical configuration

**Scope.** Configure Zensical to build the user documentation site from the
existing markdown files in `docs/user/`.

**Steps.**
1. Research Zensical's configuration format by examining the installed package
   or its documentation.
2. Create the Zensical configuration file (likely `zensical.toml` or a
   `[tool.zensical]` section in `pyproject.toml`) with:
   - Source directory: `docs/user/`
   - Output directory: `_site/` (or similar, gitignored)
   - Site title: "Unladen Velocity User Guide"
   - Navigation structure matching `docs/user/index.md`
3. Add the output directory to `.gitignore` if not already present.
4. Run `uv run zensical build` (or equivalent) and verify the site builds.

**Tests.** `uv run zensical build` succeeds and produces `_site/index.html`.
`make verify` passes.

**Exit criteria.** Running the Zensical build command produces a navigable HTML
site from the existing markdown.

## Phase 11 — Auto-generated CLI reference

**Scope.** Configure Zensical to generate CLI reference documentation from the
argparse definitions in `src/ulv/cli.py`, replacing the hand-written reference.

**Steps.**
1. Research Zensical's argparse introspection mechanism (likely a plugin or
   configuration directive pointing to the parser function).
2. Configure Zensical to extract CLI documentation from
   `ulv.cli:build_parser` (the function that returns the `ArgumentParser`).
3. Configure the output location for generated CLI reference (e.g.,
   `docs/user/cli-reference.md` or a generated directory).
4. Preserve any hand-written prose sections (examples, environment variables,
   see-also links) by:
   - Moving them to a partial template that Zensical merges with generated
     content, OR
   - Configuring Zensical to generate a separate file that the main reference
     includes, OR
   - Keeping prose in the generated output via configuration hooks.
5. Remove or archive the fully hand-written `docs/user/cli-reference.md` if
   replaced by generated output.
6. Verify the generated reference includes all commands, subcommands, options,
   types, defaults, and help text from the argparse definitions.

**Tests.** The generated CLI reference matches or exceeds the content of the
current hand-written reference. `make verify` passes. Adding a new CLI flag to
`cli.py` and rebuilding docs shows the flag in the reference without manual
edits.

**Exit criteria.** CLI reference is auto-generated from source; no manual sync
required when CLI changes (spec criterion 9).

## Phase 12 — Auto-generated API reference

**Scope.** Configure Zensical to generate API reference documentation from
docstrings and type hints in the public modules.

**Steps.**
1. Research Zensical's API documentation mechanism (likely autodoc-style
   extraction from Python modules).
2. Configure Zensical to document the following public modules:
   - `ulv.model` — `Dataset`, `Revision`, `Environment`, `Benchmark`,
     `ResultSeries`, `ResultPoint`
   - `ulv.config` — `Settings`, `load_settings`
   - `ulv.errors` — `UlvError`
   - `ulv.testbeds` — `TestbedConfig`, `parse_testbeds`, `load_testbeds_file`
   - `ulv.plugins` — `InputFormat`, `OutputGenerator`, registries
3. Exclude internal/private members (underscore-prefixed functions, internal
   modules like `ulv.gitrepo`, input/output implementations).
4. Configure output location (e.g., `docs/user/api/` or a generated section).
5. Verify the generated reference includes docstrings, type hints, method
   signatures, and class hierarchies.

**Tests.** The generated API reference documents all public classes and
functions from the target modules. `make verify` passes. Adding a docstring to
a public function and rebuilding docs shows the docstring in the reference.

**Exit criteria.** API reference is auto-generated from source; spec criterion
10 is satisfied.

## Phase 13 — Makefile integration

**Scope.** Add `make docs` and `make docs-serve` targets following the repo's
Makefile conventions.

**Steps.**
1. Add `make docs` target:
   - Command: `uv run zensical build` (or equivalent)
   - Help comment: `## Build user documentation`
   - Add to `.PHONY` declaration
2. Add `make docs-serve` target:
   - Command: `uv run zensical serve` (or equivalent for local preview server)
   - Help comment: `## Serve documentation locally for preview`
   - Add to `.PHONY` declaration
3. Verify both targets work and follow existing Makefile conventions (`uv run`
   prefix, help comment format).

**Tests.** `make docs` builds the site. `make docs-serve` starts a local
server. `make help` shows both new targets with descriptions.

**Exit criteria.** Spec criteria 12 and 13 are satisfied.

## Phase 14 — Staleness checks in verify

**Scope.** Ensure the documentation build fails if generated content is stale
relative to source code.

**Steps.**
1. Research Zensical's staleness checking mechanism (likely a `--check` flag or
   similar that exits non-zero if regeneration would change output).
2. Add a `make docs-check` target that runs the staleness check:
   - Command: `uv run zensical build --check` (or equivalent)
   - Help comment: `## Check if documentation is up to date`
   - Add to `.PHONY` declaration
3. Integrate staleness check into the verify workflow:
   - Option A: Add `docs-check` to `scripts/verify.sh` alongside lint and test
   - Option B: Add a separate `run "docs" make docs-check` step in verify.sh
4. Verify that modifying `cli.py` without rebuilding docs causes the check to
   fail.

**Tests.** `make docs-check` passes when docs are current. `make docs-check`
fails after modifying source without rebuilding. `make verify` includes the
docs check.

**Exit criteria.** Spec criteria 11 and 14 are satisfied; CI/verify fails on
stale documentation.

## Phase 15 — Final integration and cleanup

**Scope.** Ensure all Zensical-related changes are integrated, tested, and the
documentation site is complete.

**Steps.**
1. Run full `make verify` to ensure all checks pass.
2. Build the complete documentation site with `make docs`.
3. Manually review the generated site for:
   - Navigation works correctly
   - CLI reference is complete and accurate
   - API reference documents all intended public modules
   - Cross-links between hand-written and generated pages work
4. Update `docs/user/index.md` to link to generated API reference pages if they
   are in a separate location.
5. Update spec directory files if needed (remove scratch.md if present, ensure
   tasks.md is complete).

**Tests.** `make verify` passes. `make docs` produces a complete site. Manual
review confirms all spec success criteria 8-15 are satisfied.

**Exit criteria.** All Zensical-related spec criteria are satisfied; the
documentation is ready for users.

## Risks & open questions

- **Test fixture stability:** If `tests/fixtures/asv_results/` changes in a
  future commit, quickstart commands may break. Mitigation: the doc tests in
  Phase 7 will catch this.

- **Bencher cloud access:** Users without Bencher accounts cannot run the
  bencher-api examples. Mitigation: placeholder approach with clear
  instructions; no live server dependency.

- **Markdown lint tooling:** If `markdownlint-cli2` is not in the dev
  dependencies, adding it requires a justification. Mitigation: make it
  optional or skip if the project prefers manual review.

- **Zensical availability:** The spec mandates Zensical but the tool must be
  verified to exist and function as expected. If Zensical is not a real package
  or lacks required features (argparse introspection, API documentation), an
  alternative tool or custom solution may be needed. Mitigation: Phase 9 will
  fail fast if the package does not resolve; the Developer should flag this
  immediately and escalate to the Product Owner.

- **Zensical configuration format:** The exact configuration format and
  capabilities are unknown without access to Zensical documentation. Mitigation:
  Phase 10 includes research step; the Developer should document findings and
  adjust subsequent phases if the assumed features differ from reality.

- **CLI reference migration:** Replacing hand-written content with generated
  output may lose prose quality or examples. Mitigation: Phase 11 includes
  explicit steps to preserve hand-written prose sections via Zensical's
  customization mechanisms.

- **Generated file locations:** Generated documentation files may conflict with
  existing hand-written files. Mitigation: Phase 11 explicitly handles the
  transition from hand-written to generated CLI reference.
