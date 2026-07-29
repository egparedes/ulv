# Plan

Implements `spec.md` (approved, incl. its 9 Decisions). Reference code:
ASV's publish pipeline (`external/asv/asv/commands/publish.py`,
`graph.py`, `results.py`, `machine.py`) and static frontend
(`external/asv/asv/www/`). ASV fixtures for tests:
`external/asv/test/example_results/`.

## Architecture decisions

- **Runtime**: Python >= 3.11, zero runtime dependencies at bootstrap —
  3.11 gives stdlib `tomllib` for TOML config; every later dependency
  decision below keeps the runtime-dep count at zero. ADR: n/a
  (follows repo stack).
- **CLI framework**: stdlib `argparse` with subcommands (`build`,
  `serve`) — smallest thing that satisfies the spec; avoids a runtime
  dep for a two-command CLI. ADR needed: CLI framework choice
  (argparse over click/typer).
- **Config**: TOML (`tomllib`) or JSON config file; precedence
  defaults < config file < CLI flags — mandated by Decision 7; both
  parsers are stdlib. ADR: n/a (covered by CLI ADR).
- **HTTP client for Bencher API**: stdlib `urllib.request` behind a
  thin injectable `Transport` seam — read-only GETs with a token
  header don't justify httpx/requests; the seam makes stubbed-endpoint
  tests trivial. ADR needed: HTTP client for Bencher fetch.
- **Frontend**: vendor ASV's `www/` assets (BSD-3) into the package,
  plus the third-party JS/CSS its `index.html` currently pulls from
  CDNs (jQuery 3.3.1, flot 0.8.3 + plugins, flot-orderbars,
  stupidtable, blueimp-md5, Bootstrap 3.1.1 — all MIT-licensed),
  pinned to the exact versions/integrity hashes in ASV's
  `index.html`. Patch the vendored `index.html` to load everything
  locally (spec: generated site performs no network requests) and
  remove the Regressions nav item + `regressions.js`/`.css`
  (Decision 6). Keep a `LICENSES/` file with attributions. ADR
  needed: vendoring ASV frontend + third-party JS and licensing.
- **Plugin architecture**: `InputFormat` and `OutputGenerator`
  protocols; a registry pre-populated with built-ins and extended via
  `importlib.metadata` entry points (groups `ulv.input_formats`,
  `ulv.output_generators`) and a programmatic `register()` API (used
  by the dummy-plugin test) — satisfies "add without modifying shipped
  ones" with no dependency. ADR needed: plugin discovery mechanism.
- **Internal data model**: a `Dataset` mirroring ASV's publish-time
  semantics — ordered `revisions` (id, optional commit hash, date,
  branch, tags), `environments` (id → factor dict: machine, python,
  requirements, env vars, or testbed/factors), `benchmarks` (name →
  unit, type, param_names, params, pretty_name), and result series
  keyed by (benchmark, environment, revision) with optional per-point
  stats/bounds. ASV maps losslessly (unconsumed fields preserved in
  `extra` mappings); BMF maps each (benchmark name, measure slug) to
  an internal benchmark with the measure as unit and lower/upper kept
  as bounds (Decision 3). ADR: n/a (documented in
  `docs/architecture.md`, Phase 11).
- **Testbed decomposition mechanism** (Decision 8 delegates this): an
  explicit `testbed → {factor: value}` mapping table in config, with a
  declared factor list; no rule/split syntax in v1 (mapping alone
  satisfies every success criterion; rules can be added later without
  breaking config). Uncovered testbeds fail by default;
  `--allow-unmapped` / `allow_unmapped = true` includes them with
  `"unknown"` factor values (Decision 9). ADR: n/a (recorded here).
- **No step detection port**: ASV's summarylist page normally uses
  `step_detect`; we compute "last value" directly from the raw series
  and leave change columns empty — regression detection is out of
  scope (Decision 6) and this avoids porting `step_detect.py` and the
  `_rangemedian` C extension. ADR: n/a.
- **Git enrichment**: shell out to the `git` CLI (like ASV does), only
  when a repo is present/configured; no gitpython dependency
  (Decision 4). ADR: n/a.
- **Atomic output**: generators build into a temp dir next to the
  target and swap it in only on success — guarantees "never emits a
  partially broken site". ADR: n/a.
- **BMF sidecar metadata** (Decision 3): a manifest file (JSON/TOML:
  per-file commit/date/branch), or a filename-pattern template in
  config (e.g. `{commit}_{date}.json`), or CLI flags for single files;
  never mtime/lexicographic order. ADR: n/a.

## Phase 1 — Project bootstrap & CLI skeleton

**Scope.** Turn the bare template into a working uv-managed Python
project so `make verify` goes green (note: `scripts/verify.sh`
auto-activates once `pyproject.toml` exists). Ship an `ulv` console
script with `--help`/`--version` only.

**Steps.**
1. Create `pyproject.toml` via uv: project `unladen-velocity`, package
   `ulv`, `requires-python = ">=3.11"`, `src/` layout, console script
   `ulv = "ulv.cli:main"`, dev dependency group with `ruff` and
   `pytest`; commit `uv.lock`.
2. Create `src/ulv/__init__.py` (version via
   `importlib.metadata.version`) and `src/ulv/cli.py` with an argparse
   parser (no subcommands yet) supporting `--help` / `--version`.
3. Create `tests/` with `test_cli.py`: `ulv --help` exits 0 and prints
   usage; `ulv --version` prints the package version; a bogus flag
   exits non-zero.
4. Ensure ruff config (line length, target version) matches
   `docs/style.md`; run `make fmt`.

**Tests.** `tests/test_cli.py` (subprocess or `main(argv)` calls).
**Exit criteria.** `make verify` passes end-to-end for the first time.

## Phase 2 — Core data model & plugin architecture

**Scope.** The `Dataset` model and the two plugin protocols with a
registry, proven by a dummy input plugin and a dummy output generator
wired end to end (spec's extensibility criterion).

**Steps.**
1. `src/ulv/model.py`: `Revision`, `Environment`, `Benchmark`,
   `ResultSeries`, `Dataset` (frozen dataclasses where practical);
   `Dataset` exposes ordered revisions, environment-factor axes, and
   per-benchmark series lookup; carries a `has_time_axis` property
   (False for a lone BMF snapshot).
2. `src/ulv/plugins.py`: `InputFormat` protocol
   (`name`, `load(source, options) -> Dataset`), `OutputGenerator`
   protocol (`name`, `generate(dataset, out_dir, options)`); registry
   with `register()` / `get()` / `names()` and entry-point discovery
   for groups `ulv.input_formats` / `ulv.output_generators`.
3. `src/ulv/errors.py`: `UlvError(message, *, offending_input=None)`
   as the single user-facing error type (CLI later maps it to exit 1).
4. Tests: model invariants (revision ordering, axis extraction);
   registry round-trip — register a dummy input (returns a canned
   `Dataset`) and dummy output (writes a JSON dump), run
   input → model → output end to end, and assert built-ins are
   untouched; entry-point discovery exercised with a monkeypatched
   `entry_points()`.

**Tests.** `tests/test_model.py`, `tests/test_plugins.py`.
**Exit criteria.** Dummy plugin e2e test green; `make verify` passes.
ADR for plugin discovery mechanism authored before merge.

## Phase 3 — ASV input plugin (result files only, no git)

**Scope.** Read a native ASV results directory
(`results/<machine>/machine.json`, `benchmarks.json`,
`<commit>-<env>.json`) into a `Dataset`, losslessly, ordering
revisions by result date when no repository is available.

**Steps.**
1. Curate a minimal fixture under `tests/fixtures/asv_results/`
   derived from `external/asv/test/example_results/` (one machine, a
   handful of commits, at least one parameterized benchmark and one
   with env-matrix params); add a second tiny machine dir for
   multi-machine coverage.
2. `src/ulv/inputs/asv.py`: port the reading logic of
   `asv/results.py` / `asv/machine.py` / `asv/benchmarks.py` (walk
   machine dirs, validate `machine.json`, decode result api_version 2
   including compressed param/stat encodings via
   `Results.load`-equivalent code); map machines and env params
   (python, requirements, `env-*` vars) to `Environment` factors,
   benchmarks (params/param_names/unit/type) to `Benchmark`, values
   to series; preserve stats and unconsumed fields in `extra`.
3. Revision ordering without git: sort unique commit hashes by result
   `date`; expose commit hash + date on `Revision`.
4. Malformed input (bad JSON, missing `machine.json`, mismatched
   api_version) raises `UlvError` naming the offending file.
5. Register as built-in input format `asv`.

**Tests.** `tests/test_input_asv.py`: spot-check loaded values against
raw fixture JSON; param decomposition matches `benchmarks.json`;
multi-machine environments distinct; malformed-file error names the
file.
**Exit criteria.** Fixture loads into a `Dataset` whose values match
the raw files; `make verify` passes.

## Phase 4 — HTML generator core: vendored frontend + site skeleton + `ulv build`

**Scope.** Vendor the ASV frontend, generate a servable site skeleton
(`index.html`, assets, `index.json`, `info.json`) from a `Dataset`,
and wire the first end-to-end CLI path `ulv build -i asv --input-dir …
-o …` with the atomic-output and error contracts.

**Steps.**
1. Author the vendoring ADR; then copy `external/asv/asv/www/` into
   `src/ulv/outputs/html/static/` minus `regressions.js`,
   `regressions.css`; fetch the pinned CDN libs from ASV's
   `index.html` into `static/vendor/` (one-time, committed); patch
   `index.html`: local script/link tags (relative paths only), drop
   Regressions nav item and regressions includes, drop the atom-feed
   link; add `LICENSES/` attribution file. Record the exact upstream
   ASV commit in a `VENDORED.md` note.
2. `src/ulv/outputs/html/generator.py`: copy static tree to a temp
   build dir; emit `index.json` (project, params axes,
   graph_param_list, benchmarks map, machines, revision_to_hash,
   revision_to_date, tags, pages — mirroring `publish.py`) and
   `info.json`; on success atomically swap into the target output dir
   (`build/` → rename), on failure leave no output.
3. Port `Graph.get_file_path` path/sanitization logic (must stay
   byte-compatible with `asv.js:graph_to_path`) into a `paths` module
   with unit tests against known ASV-generated paths.
4. `src/ulv/cli.py`: add `build` subcommand (input format, input
   location, output dir); map `UlvError` to stderr message + exit 1.
5. Tests: build from the Phase 3 fixture; assert output contains only
   static files; scan every emitted HTML/JS/CSS for `https?://`
   asset references (none besides the patched-out ones — this is the
   no-network criterion, statically enforced); serve the output from
   a *subdirectory* via `http.server` in a test and fetch
   `index.html` + every referenced asset (200s only — non-root-path
   criterion); failure injection: unreadable input → non-zero exit,
   no output dir created.

**Tests.** `tests/test_output_html.py`, `tests/test_paths.py`,
`tests/test_cli_build.py`.
**Exit criteria.** One CLI invocation yields a site skeleton that
serves cleanly from a subdirectory; `make verify` passes. Manual
smoke: open the served site in a browser (graphs empty is OK at this
phase boundary).

## Phase 5 — Graph data: history series, parameters, machines, summary views

**Scope.** Full graph JSON generation so the vendored frontend renders
history graphs filterable by machine and benchmark parameters, plus
the grid (summary graphs) and list (summarylist JSON) views.

**Steps.**
1. Port `asv/graph.py` data handling (add_data_point, averaging over
   duplicate revisions, NA handling, scalar vs parameterized series,
   summary-graph resampling/geom-mean) *without* `detect_steps`;
   write per-series `graphs/<params…>/<benchmark>.json` files.
2. Emit one graph per (benchmark × environment-param combination ×
   branch), fill missing params with `null` across the axis union
   exactly as `publish.py` does, and populate `graph_param_list` and
   `params` in `index.json`.
3. Summary graphs for the grid view (`Graph.get_file_path(params,
   'summary')`); summarylist JSON rows with `last_value`/`last_err`
   from the raw series tail, `change_rev`/`prev_value` = null (no
   step detection, per plan decision).
4. Tests: spot-check graph JSON values equal fixture result values
   (success criterion: plotted values match input); parameterized
   benchmark produces the expected series count; two machines produce
   distinct param axes so frontend filtering has data; summary files
   exist for every benchmark.

**Tests.** extend `tests/test_output_html.py`
(`test_graph_values_match_input`, `test_param_axes`, …).
**Exit criteria.** Manual browse of the built fixture site shows
history graphs, machine/param filtering works; `make verify` passes.

## Phase 6 — Config file, flag overrides, `ulv serve`

**Scope.** Decision 7: TOML/JSON config with CLI-flag precedence, and
a local preview server.

**Steps.**
1. `src/ulv/config.py`: load `ulv.toml`/`.json` (path via `--config`,
   default `./ulv.toml`); flat, typed settings object covering input
   format + source, output dir, project name/URLs, and (later phases)
   BMF metadata, testbed mapping, Bencher endpoint; merge order:
   defaults < file < flags; unknown keys are `UlvError`s.
2. Rework `build` to consume the merged settings; every config key
   gets a corresponding flag.
3. `serve` subcommand: `http.server`-based, serves a built site dir on
   a chosen host/port (dev convenience only, per spec non-goals).
4. Tests: same key set via file and flag — flag wins; TOML and JSON
   parity; malformed config file → non-zero exit naming the file;
   `serve` smoke test (start on port 0, GET `index.html`, shut down).

**Tests.** `tests/test_config.py`, `tests/test_cli_serve.py`.
**Exit criteria.** Precedence test green both formats; `make verify`
passes. CLI-framework ADR authored (covers config precedence too).

## Phase 7 — Optional git enrichment for ASV input

**Scope.** Decision 4: same invocation, richer site when the project
repo is available — commit topological ordering, commit dates, tags,
branch attribution, commit URLs; identical behavior to Phase 3 when it
is not.

**Steps.**
1. `src/ulv/gitrepo.py`: minimal `git` CLI wrapper (rev-list ordering
   for configured branches, commit dates, tags, branch membership);
   absent/broken repo → enrichment silently skipped only when not
   explicitly configured, `UlvError` when configured but unusable.
2. ASV input: when a repo path is configured/detected, replace
   date-based revision ordering with rev-list order, fill
   `revision_to_date` from commit dates, populate tags and branch
   params, and pass `show_commit_url` through to `index.json`.
3. Tests build a throwaway git repo (pytest tmp_path + `git init`,
   synthetic commits matching fixture hashes is impractical — instead
   generate a tiny result fixture from the synthetic repo's real
   hashes) and assert: with-repo site orders by topology and carries
   dates/links; without-repo site from the same results still builds
   and orders by result date (success criterion: both cases on the
   same result set).

**Tests.** `tests/test_git_enrichment.py`.
**Exit criteria.** Same-results with/without-repo test pair green;
`make verify` passes.

## Phase 8 — BMF input plugin: sidecar metadata + snapshot view

**Scope.** Read Bencher Metric Format files with explicit sidecar
metadata into the model (Decision 3); render a lone snapshot as a
non-time-series table/bar page.

**Steps.**
1. `src/ulv/inputs/bmf.py`: parse BMF JSON (`{bench: {measure:
   {value, lower_value?, upper_value?}}}`); each (bench, measure) →
   internal benchmark, unit = measure slug, bounds preserved; register
   as input format `bmf`.
2. Sidecar metadata: manifest file (JSON/TOML: file → commit, date,
   branch), or config `filename_pattern` template with named fields,
   or CLI flags for a single file. A multi-file input with any file
   lacking metadata is a `UlvError` naming the file — never mtime or
   name-sort inference. Order revisions by metadata date (commit +
   branch recorded; git enrichment from Phase 7 applies when
   configured).
3. Snapshot path: exactly one revision → `Dataset.has_time_axis =
   False`; HTML generator emits `snapshot.html` — a static
   table/bar page (stdlib-generated HTML, vendored Bootstrap CSS,
   no new deps) listing benchmark × measure with value and
   lower/upper bounds — and makes it the site entry point for such
   datasets.
4. Tests: shuffled-file-order test — supply files in scrambled order,
   assert series order follows manifest metadata (success criterion);
   missing-metadata failure names the file; lone snapshot produces
   `snapshot.html` containing values and bounds; bounds absent →
   cells empty, not zero.

**Tests.** `tests/test_input_bmf.py`, extend
`tests/test_output_html.py` for the snapshot page.
**Exit criteria.** Shuffled-order and snapshot tests green; `make
verify` passes.

## Phase 9 — Testbed decomposition

**Scope.** Decisions 8–9: user-supplied testbed → factor mapping turns
Bencher's flat testbed axis into independent filter axes; uncovered
testbeds fail by default, `--allow-unmapped` opts into "unknown"
factor values; no mapping → single opaque `testbed` axis.

**Steps.**
1. Config schema: `[testbeds]` with `factors = [...]` and
   `[testbeds.map.<name>]` tables assigning a value per declared
   factor; validation: every mapping entry covers exactly the declared
   factors.
2. In the BMF/Bencher pipeline: with a mapping, replace the `testbed`
   environment factor with one factor per declared name; without one,
   keep `testbed` as a single axis; with `allow_unmapped`
   (flag/config), uncovered testbeds get `"unknown"` for every factor
   and a warning diagnostic naming them; without it, `UlvError`
   naming every uncovered testbed and no site emitted.
3. Tests: multi-testbed fixture — mapped build exposes each factor as
   an independent axis in `index.json` params and selecting one
   factor value matches only the right testbeds' series; unmapped
   build exposes opaque `testbed` axis; mapping omitting one testbed
   → non-zero exit naming it and no output dir; re-run with
   `--allow-unmapped` → site builds, testbed present with "unknown"
   values, diagnostic still names it.

**Tests.** `tests/test_testbeds.py`.
**Exit criteria.** All four decomposition criteria tests green; `make
verify` passes.

## Phase 10 — Bencher REST API fetcher

**Scope.** Decision 1: fetch results read-only from a Bencher server
(project + token) and produce the same site as from equivalent local
files, tested against a stubbed endpoint (no live network in tests).

**Steps.**
1. Author the HTTP-client ADR; then `src/ulv/inputs/bencher_api.py`:
   `Transport` seam (default `urllib.request` with
   `Authorization: Bearer <token>`, token from flag/config/env var —
   never logged), paginated fetch of the project's reports/metrics,
   and mapping of the richer API JSON (branch, testbed, start/end
   timestamps, benchmark/measure names) onto the same model path as
   BMF — API metadata replaces the sidecar requirement; testbed
   decomposition (Phase 9) applies unchanged. Register as input
   format `bencher-api`.
2. Record realistic API response fixtures as JSON files under
   `tests/fixtures/bencher_api/` (shape per Bencher's public API
   docs); tests run against a fake transport returning them and,
   in one integration test, against a local `http.server` stub.
3. HTTP/auth failures and malformed payloads → `UlvError` naming the
   endpoint/response; partial fetch never emits a site (atomic
   contract already covers output).
4. Tests: fetched dataset equals the dataset built from equivalent
   local files (same site `index.json`/graphs modulo timestamps);
   pagination followed; 401 → clear error; token never appears in
   error text.

**Tests.** `tests/test_input_bencher_api.py`.
**Exit criteria.** Stubbed fetch produces a site identical to the
local-file path; `make verify` passes.

## Phase 11 — Hardening, help completeness, docs

**Scope.** Close the remaining spec criteria (help coverage, error
audit), update project docs, and finish the release checklist.

**Steps.**
1. `--help` audit: test walks every subcommand's parser and asserts
   each config key has a documented flag and each documented example
   invocation parses; polish help texts.
2. Error-path sweep: table-driven test over malformed inputs (bad ASV
   json, bad BMF, bad manifest, bad config, uncovered testbed, API
   error) asserting non-zero exit, offending input named, no partial
   site (output dir absent or previous site intact).
3. Full-site browse check: build both an ASV-fixture site and a BMF
   multi-testbed site, serve from a subdirectory, crawl all referenced
   assets (200s, no external URLs) — the automated stand-in for the
   manual browser pass; do one manual browser pass per site.
4. Update `docs/architecture.md` (module map: `model`, `plugins`,
   `inputs/*`, `outputs/html`, `config`, `cli`, `gitrepo`; vendored
   frontend + ADR links); add `CHANGELOG.md` entry; confirm all four
   ADRs exist and are linked.

**Tests.** `tests/test_help.py`, `tests/test_error_paths.py`,
`tests/test_e2e_site.py`.
**Exit criteria.** Every spec success criterion has a pointing test or
a recorded manual verification; `make verify` passes; Reviewer
(`/verify`) sign-off.

## Risks & open questions

- **Vendored JS licensing/pinning**: CDN libs must be fetched once at
  the exact pinned versions and attributed; integrity hashes from
  ASV's `index.html` verify the downloads. Mitigation: ADR + checked-in
  `LICENSES/` + `VENDORED.md` with versions and hashes.
- **`asv.js` graph-path compatibility**: the frontend recomputes graph
  file paths client-side (`graph_to_path`); any sanitization mismatch
  breaks graph loading silently. Mitigation: byte-compatibility unit
  tests in Phase 4 against paths produced by ASV itself.
- **Frontend regressions-tab removal**: patching vendored JS/HTML may
  drift from upstream. Mitigation: keep patches minimal and listed in
  `VENDORED.md`; prefer removals over edits.
- **Bencher API shape drift**: fixtures are hand-recorded from public
  docs, not a live server. Mitigation: keep the transport seam so a
  recorded-against-live fixture refresh is a drop-in; name the API
  version/date in fixture files.
- **ASV result format variants** (older api_versions, compressed
  stats): fixtures cover api_version 2 only; older data errors out
  with a clear message rather than mis-parsing. Acceptable for v1;
  note in docs.
- **Summarylist without step detection** shows no "change" column
  data; if that reads as broken in the UI, hide the column in the
  vendored JS (small patch, recorded in `VENDORED.md`).
