# Tasks

Mirror of `plan.md`. Tick as you go; every phase ends with
`make verify` green.

## Phase 1 — Additive `graph_paths` manifest in `index.json`

- [x] Emit `graph_paths` (`dirs` ∥ `graph_param_list`, `summary_dir`,
      `benchmarks` name → sanitized stem) from `_index_data`, derived
      via `paths.graph_path` / `sanitize_filename`
- [x] Tests: `dirs` parallel + equal to `graph_path(entry, "x")`
      dirnames; dirs exist on disk; stems = `sanitize_filename(name)`;
      summary files exist per stem
- [x] Test: machine-less BMF site with `::` names — every emitted
      graph file reachable through the manifest
- [x] Vendored generator suites pass unmodified (additivity)
- [x] `make verify` green

## Phase 2 — `html-uplot` generator skeleton

- [x] Author ADR 0008: uPlot frontend supersedes ADR 0003's "reuse
      ASV UI"; vendoring policy carried forward; ECharts fallback
- [x] Extract `src/ulv/outputs/common.py` (atomic swap, graph build,
      summarylist, index data, snapshot rows); `HtmlOutputGenerator`
      delegates; existing tests pass unchanged
- [x] Vendor uPlot 1.6.x (`uPlot.iife.min.js`, `uPlot.min.css`) with
      sha256 verified from two sources; write `html_uplot/VENDORED.md`
      and `LICENSES/uplot.txt`
- [x] `HtmlUplotOutputGenerator` (`name = "html-uplot"`) in
      `src/ulv/outputs/html_uplot/generator.py`: static copy, shared
      data emission, own snapshot page; register as built-in
- [x] Static skeleton: `index.html` (viewport meta), `app.css`
      (responsive shell), `js/main.js` fetching `info.json`/`index.json`
      and rendering the nav tree
- [x] CLI/config: `--generator` flag + `output_generator` key
      (default `html`); unknown generator → `UlvError` listing names
- [x] Tests: payload budget < 100,000 bytes; uPlot sha256 pinned; no
      absolute URLs anywhere in the new static tree (JS included);
      static-suffix check; snapshot page (values, bounds
      empty-not-zero, local CSS); atomic-swap tests on new generator;
      default build still vendored frontend
- [x] E2e: crawl `html-uplot` ASV + BMF sites from a subdirectory,
      following module scripts and static imports; manifest dirs and
      all graph files return 200
- [x] Wheel test: static tree, vendor files, `VENDORED.md`,
      `LICENSES/uplot.txt` ship; site builds from installed wheel
- [x] Config/CLI precedence tests for `--generator`
- [ ] Manual smoke: served site shows nav tree
- [x] `make verify` green

## Phase 3 — Graph view core

- [x] `js/data.js`: manifest-only graph fetches (encodeURIComponent
      per segment); missing file → "no data", not an error
- [x] `js/state.js`: hash codec (view, benchmark, params, log, x-axis,
      zoom); every UI mutation writes the hash
- [x] `js/views/graph.js`: generic selector panels from
      `index.params` (`null` as `[none]`); benchmark-param
      sub-selection; uPlot series per permutation; units in y-axis
      label; log toggle; date/even-spacing toggle; tooltip with value
      + units + short hash; point click → commit URL
- [x] Static test: app-shell JS contains no `machine` token
- [x] Crawl covers new modules; budget still green
- [ ] Manual: graphs render and behave on ASV and BMF fixture sites
- [x] `make verify` green

## Phase 4 — Overview ranger, series toggling, touch plugin

- [x] `js/views/overview.js`: mini plot, drag-select zoom, zoom in hash
- [x] Legend with per-series show/hide, state in hash
- [x] `js/touch.js`: pinch-zoom/pan plugin (uPlot hooks); provenance
      line in `html_uplot/VENDORED.md`
- [x] Static tests: modules crawled, budget green, `touch.js`
      referenced, no absolute URLs
- [ ] Manual: drag-zoom, legend toggling, pinch/pan via touch emulation
- [x] `make verify` green

## Phase 5 — Grid and list views

- [x] `js/views/grid.js`: lazy thumbnails (IntersectionObserver) from
      `summary_dir` + stem; card click → graph view
- [x] `js/views/list.js`: summary rows via manifest; name/value
      (+ units)/error columns; self-authored sort; no dead columns
- [x] Static test: no "Recent change" / "Changed at" in shipped app
      code; crawl + budget green
- [x] E2e: every manifest-derived thumbnail URL returns 200 on the
      BMF (`::`-named) site
- [ ] Manual: thumbnails lazy-load, sorting works, units visible
- [x] `make verify` green

## Phase 6 — Docs, vendoring polish, parity checklist

- [x] `docs/architecture.md`: module map (+`common`, +`html_uplot`),
      `graph_paths` contract, units gap closed, ADR 0008 linked
- [x] User docs: `--generator html-uplot` / `output_generator` example;
      vendored generator remains default
- [x] `CHANGELOG.md`: bullets for new generator + manifest
- [x] Final `html_uplot/VENDORED.md` + `LICENSES/` review (banner
      v1.6.32 = pin, hashes match, MIT text + copyright present)
- [x] `make verify` green

### Manual parity checklist — HUMAN PASS REQUIRED

Every unticked item below blocks feature sign-off (plan Phase 6).
All are browser-interactive and could not be verified by the agent.

> **Automated pre-pass:** `ui-parity-check` ran on 2026-07-19 against both
> fixture sites — see [`parity-report-2026-07-19.md`](parity-report-2026-07-19.md)
> for per-item evidence. Boxes are left unticked for the human sign-off.
> Agent verdicts (report order): 1 pass · 2 pass · 3 pass (live-Bencher
> units string = confirm manually) · 4 pass · 5 pass · 6 pass · 7 pass ·
> 8 confirm manually (device feel) · 9 confirm manually (device feel) ·
> 10 list/columns pass, lazy-thumbnail runtime = confirm manually
> (fixtures ≤4 benchmarks) · 11 pass · 12 pass · 13 pass · 14 pass.
> Two findings from the run were **fixed** in this branch: the zoom
> reset-double-click no longer opens commit tabs (`graph.js` click
> debounce), and the overview strip now re-fits on resize (no phone
> overflow while zoomed). A third — no fixture large enough to exercise
> runtime lazy-thumbnail mounting — remains open.

**Setup** (from the repo root; both sites deliberately served from a
subdirectory):

```bash
uv run ulv build -i asv --input-dir tests/fixtures/asv_results \
  -o /tmp/ulv-parity/asv-site --project demo \
  --show-commit-url "https://github.com/airspeed-velocity/asv/commit/" \
  --generator html-uplot
uv run ulv build -i bmf --input-dir docs/user/samples/bmf \
  --manifest docs/user/samples/bmf/manifest.json \
  -o /tmp/ulv-parity/bmf-site --project bmfdemo --generator html-uplot
python3 -m http.server 8123 -d /tmp/ulv-parity
```

Open <http://127.0.0.1:8123/asv-site/> (machine axes) and
<http://127.0.0.1:8123/bmf-site/> (machine-less). Keep devtools open
with **"Disable cache" checked** — a cached JS file once masked a fix
during earlier manual verification. Run every item on BOTH sites
unless it names one.

- [ ] Nav tree renders grouped benchmarks; clicking a leaf opens its
      graph. Param selector buttons filter series; on the ASV site,
      `params_examples.mem_param` shows number/depth sub-selection
      buttons that add/remove series
- [ ] Log toggle switches the y scale (spacing changes, no errors);
      "date"/"even x-axis" buttons switch between date axis and
      evenly spaced short-hash labels
- [ ] Hover shows crosshair + tooltip: short (8-char) hash, date, and
      per-series value with units text (BMF shows the measure slug,
      e.g. `latency`, via the same `units || unit` path; if a real
      Bencher project is available, confirm the human-readable units
      string, e.g. "nanoseconds (ns)")
- [ ] Clicking a data point (ASV site) opens
      `https://github.com/airspeed-velocity/asv/commit/<full hash>`;
      no commit page opens after finishing a drag-zoom on the main
      chart, and none ever opens from the overview strip
- [ ] Drag on the main chart zooms; drag on the overview strip zooms
      the main chart and paints the window on the strip; double-click
      resets; the `zoom=` hash key appears/disappears accordingly
- [ ] Legend click hides/shows a series (`hide=` appears in the hash)
- [ ] Legend toggle → axis/benchmark change → no series unexpectedly
      hidden (hidden indices are positional; must reset on selection
      change)
- [ ] Pinch-zoom/pan (devtools touch emulation or device): two-finger
      pinch zooms x around the midpoint, one-finger drag pans,
      vertical swipe still scrolls the page; the final range lands in
      the hash on gesture end
- [ ] Touch: 2→1 finger transition mid-gesture doesn't jump (if it
      does: re-anchor on touchend while touches remain — non-blocking)
- [ ] Grid view (landing page): thumbnails appear as cards scroll
      into view (throttle network in devtools to see laziness); card
      click opens the graph view. List view: header clicks sort
      ascending/descending (numbers numerically, nulls last); columns
      are exactly Benchmark / Last value / Error — no
      change-detection columns; values show units text
- [ ] Hash round-trip: set benchmark + param selection + log + even
      x + zoom + one hidden series, copy the URL into a fresh tab —
      identical view restores
- [ ] Phone-width viewport (devtools, e.g. 375 px): nav collapses
      above the content, no horizontal scrolling of page chrome,
      selectors and charts reachable
- [ ] BMF site: no machine selector anywhere (os/arch or testbed
      axes only); ASV site: machine appears as an ordinary axis group
- [ ] Devtools network tab while browsing all three views: only the
      site's own static files under `/asv-site/` (resp. `/bmf-site/`)
      are fetched — no external hosts
