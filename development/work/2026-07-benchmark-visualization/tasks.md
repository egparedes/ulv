# Tasks

Mirrors `plan.md`. Tick as you go; every phase ends with `make verify`
green.

## Phase 1 — Project bootstrap & CLI skeleton

- [x] Create uv-managed `pyproject.toml` (`unladen-velocity`, package
      `ulv`, `requires-python >=3.11`, src layout, `ulv` console
      script, dev group: ruff + pytest); commit `uv.lock`
- [x] Add `src/ulv/__init__.py` and `src/ulv/cli.py` (argparse,
      `--help` / `--version`)
- [x] Add `tests/test_cli.py` (help exits 0, version matches, bad flag
      non-zero)
- [x] Align ruff config with `docs/style.md`; run `make fmt`
- [x] `make verify` green (verify.sh now active)

## Phase 2 — Core data model & plugin architecture

- [x] `src/ulv/model.py`: Revision / Environment / Benchmark /
      ResultSeries / Dataset (+ `has_time_axis`)
- [x] `src/ulv/plugins.py`: InputFormat + OutputGenerator protocols,
      registry (`register`/`get`/`names`), entry-point discovery
      (`ulv.input_formats`, `ulv.output_generators`)
- [x] `src/ulv/errors.py`: `UlvError` with `offending_input`
- [x] Tests: model invariants; dummy input + dummy output e2e via
      registry; entry-point discovery (monkeypatched)
- [x] Author ADR: plugin discovery mechanism
- [x] `make verify` green

## Phase 3 — ASV input plugin (files only, no git)

- [x] Curate `tests/fixtures/asv_results/` from
      `external/asv/test/example_results/` (2 machines, parameterized
      + env-matrix benchmarks)
- [x] `src/ulv/inputs/asv.py`: read machine.json / benchmarks.json /
      result files (api_version 2), map losslessly to Dataset
- [x] Date-based revision ordering (no git)
- [x] Malformed input → `UlvError` naming the file
- [x] Register built-in input `asv`
- [x] Tests: values match raw JSON; params; multi-machine; error paths
- [x] `make verify` green

## Phase 4 — HTML generator core + `ulv build`

- [x] Author ADR: vendoring ASV frontend + third-party JS licensing
- [x] Vendor `asv/www/` into `src/ulv/outputs/html/static/` (drop
      regressions.*), fetch pinned CDN libs into `static/vendor/`,
      patch `index.html` for local-only relative assets, add
      `LICENSES/` + `VENDORED.md`
- [x] Generator: copy static tree, emit `index.json` + `info.json`,
      build in temp dir, atomic swap, nothing on failure
- [x] Port `Graph.get_file_path` path logic (byte-compatible with
      `asv.js:graph_to_path`) + unit tests
- [x] CLI `build` subcommand; `UlvError` → stderr + exit 1
- [x] Tests: static-only output; no `https?://` asset refs; served
      from subdirectory, all assets 200; failure → no output dir
- [x] `make verify` green; manual browser smoke of skeleton site

## Phase 5 — Graph data: series, params, machines, summaries

- [x] Port graph data handling from `asv/graph.py` (no detect_steps);
      write `graphs/…/<benchmark>.json`
- [x] Per (benchmark × params × branch) graphs; null-fill param axes;
      `graph_param_list` + `params` in index.json
- [x] Summary graphs (grid view) + summarylist JSON (last value from
      raw tail, change fields null)
- [x] Tests: graph values == fixture values; parameterized series
      count; distinct machine axes; summary files per benchmark
- [x] `make verify` green; manual browse: graphs + machine/param
      filtering work

## Phase 6 — Config, flag overrides, `ulv serve`

- [x] `src/ulv/config.py`: TOML/JSON load, defaults < file < flags,
      unknown keys error
- [x] `build` consumes merged settings; flag per config key
- [x] `serve` subcommand (http.server on host/port)
- [x] Tests: flag-beats-file (TOML and JSON); malformed config exits
      non-zero naming file; serve smoke test
- [x] Author ADR: CLI framework choice (argparse + config precedence)
- [x] `make verify` green

## Phase 7 — Optional git enrichment (ASV input)

- [x] `src/ulv/gitrepo.py`: git-CLI wrapper (rev-list order, dates,
      tags, branch membership); configured-but-unusable repo → error
- [x] Wire enrichment into ASV input + index.json
      (`revision_to_date`, tags, branch param, `show_commit_url`)
- [x] Tests: synthetic git repo fixture; with-repo vs without-repo on
      same results — both build, ordering/dates/links differ as
      specified
- [x] `make verify` green

## Phase 8 — BMF input + snapshot view

- [x] `src/ulv/inputs/bmf.py`: parse BMF; (bench, measure) → internal
      benchmark; bounds preserved; register `bmf`
- [x] Sidecar metadata: manifest file, `filename_pattern`, CLI flags;
      missing metadata → error naming file; order by metadata only
- [x] Snapshot path: single revision → `snapshot.html` table/bar page
      with values + bounds as site entry point
- [x] Tests: shuffled file order follows metadata; missing-metadata
      failure; snapshot page content; absent bounds not rendered as 0
- [x] `make verify` green

## Phase 9 — Testbed decomposition

- [x] Config schema: `[testbeds] factors` + `[testbeds.map.<name>]`;
      validate coverage of declared factors
- [x] Pipeline: mapping → per-factor axes; no mapping → opaque
      `testbed` axis; `--allow-unmapped` → "unknown" values + warning;
      default → `UlvError` naming uncovered testbeds, no site
- [x] Tests: factor filtering matches only mapped testbeds; opaque
      axis; omitted testbed fails naming it; `--allow-unmapped`
      builds with "unknown" + diagnostic
- [x] `make verify` green

## Phase 10 — Bencher REST API fetcher

- [x] Author ADR: HTTP client for Bencher fetch (stdlib urllib +
      transport seam)
- [x] `src/ulv/inputs/bencher_api.py`: transport seam, bearer token
      (flag/config/env, never logged), paginated fetch, map API JSON
      via BMF model path; register `bencher-api`
- [x] Record API response fixtures under `tests/fixtures/bencher_api/`
- [x] Errors: HTTP/auth/malformed payload → `UlvError`; no partial
      site
- [x] Tests: fetched site == equivalent local-file site; pagination;
      401 handling; token absent from error text; http.server stub
      integration test
- [x] `make verify` green

## Phase 11 — Hardening, help completeness, docs

- [x] Help audit test: every config key has a flag, every documented
      invocation parses
- [x] Table-driven error-path test (ASV/BMF/manifest/config/testbed/
      API): non-zero exit, input named, no partial site
- [x] Crawl test: ASV site + BMF multi-testbed site served from
      subdirectory, all assets 200, no external URLs; manual browser
      pass on both (sites prepared for the coordinator's pass)
- [x] Wire Phase 7 git enrichment into the BMF input (plan Phase 8
      step 2 says it "applies when configured") or record the deferral
      → recorded in docs/architecture.md "Deferred / future work";
      `bmf` and `bencher-api` reject `repo`/`branches` with explicit
      UlvErrors
- [x] Update `docs/architecture.md` (module map, ADR links);
      `CHANGELOG.md` entry; confirm 4 ADRs exist
- [x] `make verify` green; run `/verify` (Reviewer)
