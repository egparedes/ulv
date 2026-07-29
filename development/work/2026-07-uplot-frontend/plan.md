# Plan

Implements `spec.md` (approved, incl. its 10 Decisions). Reference
code: the existing generator (`src/ulv/outputs/html/generator.py`,
`graphs.py`, `paths.py`), its vendoring record
(`src/ulv/outputs/html/VENDORED.md` — the 8 patches whose bug classes
the new frontend must eliminate), and the crawl harnesses in
`tests/test_output_html.py` / `tests/test_e2e_site.py`. Fixtures:
`tests/fixtures/asv_results/` (machines), the BMF site builders in
`tests/test_e2e_site.py` (machine-less, Bencher-style `::` names), and
`tests/fixtures/bencher_api/` (units strings).

## Architecture decisions

- **Index manifest shape (resolves the spec's flagged question)**: one
  additive top-level `index.json` key, `graph_paths`, containing
  `dirs` (array parallel to `graph_param_list`; each entry's on-disk
  graph directory, e.g. `"graphs/branch-main/machine-cheetah/…"`),
  `summary_dir` (`"graphs/summary"`), and `benchmarks` (benchmark
  name → sanitized file stem, no `.json`). Any graph URL is
  `dir + "/" + stem + ".json"` with per-segment `encodeURIComponent`
  applied client-side. A parallel array (not a key inside each
  `graph_param_list` entry) because the vendored `graph_to_path`
  iterates entry keys — injecting a key there would corrupt vendored
  path computation; a full graph-key → path map would be a needless
  |params|×|benchmarks| cross product. Additive only: the vendored
  frontend never reads unknown keys, and its tests assert a superset
  of keys. ADR: n/a (contract documented in `docs/architecture.md`,
  Phase 6).
- **Generator identity**: registry name `html-uplot`, class
  `HtmlUplotOutputGenerator` in `src/ulv/outputs/html_uplot/`
  (`generator.py`, `static/`, `VENDORED.md`, `LICENSES/`). Registered
  as a built-in via the existing programmatic registration (ADR 0002);
  no pyproject entry point, matching the other built-ins. ADR: n/a.
- **Generator selection**: new `--generator` CLI flag + `output_generator`
  config key, default `"html"` — replaces the hardcoded
  `output_generators.get("html")` in `cli.py`. Default unchanged
  (spec: vendored generator stays default). ADR: n/a (extends ADR 0004's
  existing precedence scheme).
- **Code sharing — shared modules, not copies**: extract the atomic
  build/swap and the site-data emission (`_build_graphs`,
  `_write_summarylist`, `_index_data`, snapshot row extraction) from
  `HtmlOutputGenerator` into a shared `src/ulv/outputs/common.py`;
  `graphs.py` and `paths.py` stay where they are and are imported by
  both generators. Both generators become thin assemblers over one
  data pipeline. Mechanical move; the existing generator's behavior
  stays locked by its unchanged test suite. ADR: n/a.
- **Data contract**: the new frontend consumes the *same*
  `index.json` + `graphs/**/*.json` + `info.json` files as the
  vendored one (plus `graph_paths`); no second data pipeline (spec
  non-goal: data layer unchanged). Missing graph files for a
  param-combo × benchmark that has no data are "no data", not errors —
  same tolerance as the vendored frontend. ADR: n/a.
- **Chart library**: uPlot, pinned to the exact latest 1.6.x release
  at vendoring time, as two files — `uPlot.iife.min.js` (single IIFE)
  and `uPlot.min.css` — under `html_uplot/static/vendor/`, sha256
  recorded in `html_uplot/VENDORED.md` and asserted by a test (hash of
  the on-disk file equals the pinned constant). Update policy: manual
  re-vendor of a newer pinned release; local patches avoided —
  behavior gaps are closed in our own plugin/app code instead.
  ADR needed: supersede ADR 0003's "reuse ASV UI" frontend choice,
  carrying its vendoring policy forward (authored in Phase 2, before
  the vendored files land; ECharts recorded as fallback).
- **Touch pinch-zoom/pan**: a self-authored `touch.js` uPlot plugin in
  the app shell (hooks approach, derived from uPlot's MIT zoom-touch
  demo; provenance noted in `html_uplot/VENDORED.md`). Our code, our
  file, counts toward the payload budget. ADR: covered by the new ADR.
- **App shell format**: ES modules (`<script type="module">`), plain
  files, no build toolchain (spec Decision 2). Consequence: the site
  requires http(s) serving — already true today (the vendored frontend
  XHRs `index.json`), so no regression. uPlot's IIFE loads as a
  classic script before the modules. ADR: n/a.
- **View state in the URL hash**: self-authored
  URLSearchParams-in-fragment encoding
  (`#view=…&benchmark=…&<param>=…&log=…&x=date&zoom=…`); no library.
  ADR: n/a.
- **Snapshot page**: server-generated static HTML (as today), styled
  by the new generator's own CSS, zero JS. ADR: n/a.
- **Payload budget constant**: 100,000 bytes (decimal — the
  conservative reading of "<100 KB"), enforced by a test summing every
  file under `html_uplot/static/`. ADR: n/a.
- **Testing boundary — no new test dependencies**: verification uses
  only the existing stdlib-HTTP crawl harness plus static assertions
  (payload budget, hash pin, no absolute URLs anywhere in our own
  JS/CSS/HTML, manifest-declared paths resolvable, module-import graph
  crawlable, no `machine` special-casing in app code, dead columns
  absent). Interactive behaviors — actual chart rendering, hover
  tooltip, drag/pinch zoom, series toggling, hash round-trip,
  narrow-viewport layout — are verified by the documented manual
  checklist in Phase 6; the spec explicitly allows the documented
  manual check for touch. Adding browser automation (e.g. Playwright
  as a dev dependency) is deliberately out of this feature; if wanted
  later it is its own decision. ADR needed *only if* browser
  automation is added later.

## Phase 1 — Additive `graph_paths` manifest in `index.json`

**Scope.** Emit the manifest from the existing generator's index data
so the path contract exists before any new frontend code, and prove it
is purely additive: the vendored generator's suite passes unchanged
and every manifest-declared path resolves on disk — including for
Bencher-style names that sanitize differently from their raw form.

**Steps.**
1. In `src/ulv/outputs/html/generator.py` (`_index_data`), emit
   `graph_paths` per the decided shape, deriving `dirs` and stems from
   the existing `paths.graph_path` / `sanitize_filename` so manifest
   and files cannot drift.
2. Tests in `tests/test_output_html.py`: `graph_paths.dirs` is
   parallel to `graph_param_list` and each dir equals the dirname of
   `graph_path(entry, "x")`; every `dirs[i]` exists on disk;
   `benchmarks` maps every benchmark to `sanitize_filename(name)`;
   `summary_dir` files exist per benchmark stem.
3. Test on a machine-less BMF site with `::` names (reuse the
   `test_e2e_site.py` builder): every existing `graphs/**/*.json` file
   is reachable *through* the manifest (dir × stem membership), i.e.
   no emitted graph file is unreachable via manifest lookups.
4. Confirm additivity: run the vendored generator's suites unmodified
   (`test_output_html.py` pre-existing tests, `test_e2e_site.py`).

**Tests.** Extended `tests/test_output_html.py`
(`TestGraphPathsManifest`); existing suites unchanged and green.
**Exit criteria.** Manifest emitted and internally consistent on ASV
and BMF fixtures; `make verify` green.

## Phase 2 — `html-uplot` generator skeleton: ADR, vendoring, selection, snapshot, budget

**Scope.** A selectable second generator that produces a complete,
crawlable site — full data files via the shared pipeline, a static
app-shell `index.html` that boots (nav renders; views land in Phases
3–5), the snapshot page, and the guard-rail tests (payload budget,
hash pin, no absolute URLs, wheel packaging). The vendored generator's
behavior is untouched.

**Steps.**
1. Author the new ADR (`docs/adr/0008-…`): uPlot vendored frontend
   supersedes ADR 0003's "reuse ASV UI" choice; carries the vendoring
   policy (pinned files, recorded sources + integrity hashes,
   `VENDORED.md`, `LICENSES/`); ECharts as documented fallback.
2. Extract `src/ulv/outputs/common.py` from the existing generator:
   atomic build/swap, graph building, summarylist emission, index
   data, snapshot row extraction; `HtmlOutputGenerator` delegates to
   it. Pure refactor — existing tests pass unchanged.
3. Vendor uPlot: download the pinned 1.6.x `uPlot.iife.min.js` +
   `uPlot.min.css`, verify sha256 against the published npm/jsDelivr
   artifact, commit under `html_uplot/static/vendor/`; write
   `html_uplot/VENDORED.md` (version, source URLs, hashes, update
   policy) and `html_uplot/LICENSES/uplot.txt` (MIT text + copyright).
4. Create `src/ulv/outputs/html_uplot/generator.py`:
   `HtmlUplotOutputGenerator` (name `html-uplot`) — copy static tree,
   emit the same data files via `common.py`, write its own snapshot
   page (new CSS, no JS) for `has_time_axis == False`; register as a
   built-in in `plugins._register_builtins`.
5. Static skeleton: `index.html` (with `<meta name="viewport">`),
   `app.css` (responsive shell: header, nav, main pane), `js/main.js`
   (+ initial modules) that fetches `info.json`/`index.json` via
   relative paths and renders the benchmark nav tree.
6. CLI/config: `--generator` flag + `output_generator` setting
   (default `html`); unknown name → the registry's `UlvError` listing
   available generators.
7. Tests (`tests/test_output_html_uplot.py`): payload budget — sum of
   bytes under `html_uplot/static/` < 100,000; sha256 of vendored
   uPlot files equals pinned constants and matches `VENDORED.md`; no
   `https?://` or protocol-relative URL anywhere in the new static
   tree (ours end to end, so JS is scanned too — stricter than the
   vendored suite); output contains only static-servable suffixes;
   snapshot-page tests mirrored from `TestSnapshotPage` (values,
   bounds empty-not-zero, local CSS only); atomic-swap tests reused
   against the new generator; default-generator test — a build with no
   `--generator` still emits the vendored frontend (`asv.js` present).
8. Extend `tests/test_e2e_site.py`: crawl the `html-uplot` site
   (ASV + BMF builders, `--generator html-uplot`) served from a
   subdirectory — extend the crawler to follow `<script type="module">`
   tags and static `import … from "./…"` specifiers so every shipped
   JS module is fetched; assert every manifest-declared dir and every
   emitted graph file returns 200.
9. Extend the wheel test (`TestPackaging`): wheel contains
   `html_uplot/static/index.html`, `static/vendor/uPlot.iife.min.js`,
   `VENDORED.md`, `LICENSES/uplot.txt`; build a site from the
   installed wheel path (existing test already builds the wheel).

**Tests.** `tests/test_output_html_uplot.py`, extended
`tests/test_e2e_site.py`, extended `TestPackaging`, extended
`tests/test_config.py`/CLI tests for `--generator` precedence.
**Exit criteria.** `ulv build … --generator html-uplot` yields a site
whose shell loads and crawls cleanly from a subdirectory on ASV and
BMF fixtures; budget test green with headroom; default build
unchanged; ADR 0008 merged; `make verify` green. Manual smoke: open
the served site — nav tree visible (empty chart pane is OK here).

## Phase 3 — Graph view core

**Scope.** The main history-graph view: uPlot wiring, generic
parameter selectors (machine is just an axis), benchmark-parameter
sub-selection, log-scale and date/even-spacing toggles, hover
crosshair + tooltip with units, commit click-through, and URL-hash
state round-trip. Largest phase; it stays inside the app shell —
no Python changes.

**Steps.**
1. `js/data.js`: resolve and fetch graph files strictly through
   `graph_paths` (dir lookup by `graph_param_list` index + benchmark
   stem; per-segment `encodeURIComponent`); missing file → "no data"
   placeholder, never an error.
2. `js/state.js`: hash codec (view, benchmark, one key per param axis,
   benchmark-param indices, `log`, `x`, zoom range); state → render is
   one-directional; every UI mutation writes the hash.
3. `js/views/graph.js`: build selector panels generically from
   `index.params` (multi-select per axis; `null` shown as `[none]`),
   benchmark-param sub-selection from `params`/`param_names`; one
   uPlot series per selected param permutation; y-axis label from
   `benchmarks[name].units || unit`; log toggle (uPlot log distr),
   date vs. even-spacing toggle (`revision_to_date` vs. revision
   index); tooltip showing value + units + short hash
   (`hash_length`); point click opens `show_commit_url` + full hash.
4. Static tests: app-shell JS contains no `machine` token (enforces
   Decision 4 — no special-casing; the axis works because axes are
   generic); crawl still covers all new modules; budget still green.
5. BMF fixture assertions: `html-uplot` site for the machine-less
   builders emits no machine axis in `index.json` (already true) and
   the app renders selectors purely from `params` — covered by the
   no-`machine`-token test plus manual check.

**Tests.** Extended `tests/test_output_html_uplot.py` (static
assertions), extended e2e crawl. Manual (recorded in Phase 6
checklist): chart renders, selectors filter, toggles work, tooltip,
click-through, hash round-trip.
**Exit criteria.** Browsing an ASV-fixture site and a BMF-fixture site
shows working history graphs end to end in a manual pass; all static
suites green; `make verify` green.

## Phase 4 — Overview ranger, series toggling, touch plugin

**Scope.** Parity interactions on the graph view: overview mini-plot
with drag-select zoom (uPlot's cursor/select + a second synced mini
uPlot), series legend with per-series show/hide, and the self-authored
touch pinch-zoom/pan plugin.

**Steps.**
1. `js/views/overview.js`: mini plot of the current selection with
   drag-select → main-plot zoom; zoom range persisted in the hash.
2. Legend with per-series toggling (uPlot `series.show`); toggle state
   in the hash.
3. `js/touch.js`: pinch-zoom + pan plugin via uPlot hooks (derived
   from the MIT demo; provenance line added to
   `html_uplot/VENDORED.md`).
4. Static tests: new modules crawled; budget green; no absolute URLs;
   `touch.js` referenced from the graph view.

**Tests.** Extended static/crawl suites. Manual (Phase 6 checklist):
drag-zoom, legend toggling, pinch-zoom/pan on a touch device or
devtools touch emulation.
**Exit criteria.** Manual pass shows ranger, toggling, and touch
gestures working; `make verify` green.

## Phase 5 — Grid and list views

**Scope.** The two remaining pages: lazy-loaded thumbnail grid and
sortable list view — without the dead "Recent change"/"Changed at"
columns — plus units shown alongside values.

**Steps.**
1. `js/views/grid.js`: one card per benchmark, thumbnail mini-chart
   from `summary_dir` + stem, lazily rendered via
   `IntersectionObserver`; card click → graph view (hash update).
2. `js/views/list.js`: fetch the summary rows file for the current
   param selection (via `graph_paths`), render a table of
   name / last value (+ units, from `benchmarks[name].units || unit`)
   / error; self-authored column sort (string/number aware); no
   "Recent change" / "Changed at" columns.
3. Static tests: shipped app code contains neither "Recent change"
   nor "Changed at" (dead-column subtraction, spec Decision 5); crawl
   covers new modules; budget green.
4. E2e: for the BMF builder site, assert every `summary_dir` thumbnail
   URL derived from the manifest returns 200 (the patch-6 bug class,
   now manifest-driven).

**Tests.** Extended static/crawl suites. Manual (Phase 6 checklist):
lazy thumbnails render on scroll, sorting works, units visible.
**Exit criteria.** All three views navigable in a manual pass on both
fixture kinds; `make verify` green.

## Phase 6 — Docs, vendoring polish, parity checklist

**Scope.** Close the documentation criteria and run the recorded
manual parity pass that stands in for browser automation.

**Steps.**
1. `docs/architecture.md`: add `ulv.outputs.common` and
   `ulv.outputs.html_uplot` to the module map; document the
   `graph_paths` contract; move the "Bencher measure units" item out
   of deferred work (closed by Phase 3); link ADR 0008.
2. User docs: document `--generator html-uplot` / `output_generator`
   with a runnable example; note the vendored generator remains the
   default.
3. `CHANGELOG.md` `[Unreleased]`: one bullet for the new generator,
   one for the additive `graph_paths` manifest.
4. Final review of `html_uplot/VENDORED.md` + `LICENSES/` (uPlot
   version/hashes/source, touch-plugin provenance) against the rigor
   of the existing `VENDORED.md`.
5. Run and record the manual parity checklist (tick in `tasks.md`),
   once against the ASV fixture site and once against a machine-less
   BMF site, both served from a subdirectory:
   - nav tree; param selectors; benchmark-param sub-selection
   - log toggle; date/even-spacing toggle
   - hover tooltip (values + units on the Bencher-units fixture)
   - commit click-through URL honors template + hash length
   - overview drag-zoom; legend series toggling
   - pinch-zoom/pan via devtools touch emulation (or real device)
   - grid lazy thumbnails; list sorting; no dead columns visible
   - hash round-trip for a representative set of states
     (copy URL → fresh tab → same view)
   - phone-width viewport: no horizontal scrolling of page chrome
   - machine-less site shows no machine selector; machine site shows
     machine as an ordinary axis
   - browser devtools network tab: no requests beyond the site's own
     static files

**Tests.** Existing suites (no new automated tests); the checklist is
the recorded manual verification the spec allows.
**Exit criteria.** Every spec success criterion maps to a green test
or a ticked checklist item; docs and CHANGELOG updated; `make verify`
green; ready for `/verify` (Reviewer).

## Risks & open questions

- **uPlot artifact/SRI availability**: npm tarballs are not
  SRI-annotated the way ASV's CDN tags were. Mitigation: compute
  sha256 at download from two independent sources (npm registry +
  jsDelivr), record both provenance URLs in `VENDORED.md`, and pin
  the hash in a test.
- **Payload creep**: the app shell must fit in ~45 KB beside uPlot.
  Mitigation: the budget test lands in Phase 2, so every later phase
  fails fast if the shell bloats; no third-party additions without
  revisiting the ADR.
- **Interactive behavior only manually verified**: rendering, zoom,
  touch, hash round-trip and viewport layout have no automated
  coverage by design (no new test deps). Mitigation: the Phase 6
  recorded checklist, run on both fixture kinds; Reviewer treats
  unticked items as blocking. Browser automation remains a possible
  future decision (own ADR).
- **Parity gaps discovered late**: subtle vendored-frontend behaviors
  (e.g. selector defaulting, `[none]` handling) may only surface in
  the manual pass. Mitigation: parity targets are enumerated per view
  in Phases 3–5; anything found in Phase 6 is triaged against the
  spec's parity list before sign-off.
- **`common.py` extraction regressions**: the refactor touches the
  default generator. Mitigation: pure mechanical move in its own step
  (Phase 2.2) with the vendored suite as an unchanged behavioral lock.
- **Module-crawl blind spots**: dynamic `import()` or computed fetch
  URLs would evade the static import scanner. Mitigation: app-shell
  convention — static imports and manifest-derived fetches only; the
  no-absolute-URL scan covers the rest.
- **Product flag (not architectural, left open)**: whether/when to
  flip the default generator is explicitly out of scope (spec
  non-goal) and stays a later owner decision.
