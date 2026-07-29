# UI parity report — html-uplot frontend

- **Date:** 2026-07-19
- **Target spec:** `specs/2026-07-uplot-frontend/`
- **Harness:** Claude Code (Playwright MCP `@playwright/mcp@0.0.78`,
  `--headless --isolated --caps=vision --browser chromium`)
- **Browser:** Chrome for Testing 151.0.7922.10 (playwright chromium v1232)
- **Repo commit:** `0e2a3c5`
- **Server:** `python3 -m http.server 8123 -d /tmp/ulv-parity` (started
  cold, stopped at end; port confirmed free before and after)

## Sites built

```
uv run ulv build -i asv --input-dir tests/fixtures/asv_results \
  -o /tmp/ulv-parity/asv-site --project demo \
  --show-commit-url "https://github.com/airspeed-velocity/asv/commit/" \
  --generator html-uplot
uv run ulv build -i bmf --input-dir docs/user/samples/bmf \
  --manifest docs/user/samples/bmf/manifest.json \
  -o /tmp/ulv-parity/bmf-site --project bmfdemo --generator html-uplot
```

- ASV (machine axes): `http://127.0.0.1:8123/asv-site/` — 4 benchmarks.
- BMF (machine-less): `http://127.0.0.1:8123/bmf-site/` — 3 benchmarks.

## Calibration result (mandatory, per run)

Confirmed empirically at the start of the run:

- **`*_xy` coordinate semantics = viewport-level CSS px**, matching
  `Element.getBoundingClientRect`. Evidence: `getBoundingClientRect` on
  the "List" nav link gave centre (166.86, 19.5);
  `browser_mouse_click_xy(166.86, 19.5)` landed the click →
  `location.hash` became `#view=list`.
- **`browser_mouse_drag_xy` produces a drag-zoom** on the main chart:
  a drag across `.u-over` put `zoom=1372689292.983,1378631359.204` in
  the hash and narrowed the x range.
- **`clickCount: 2` performs a double-click** that resets zoom (`zoom=`
  left the hash).
- **Chart-point coordinates** derived from
  `.chart-wrap .u-over` `getBoundingClientRect()`; the module-scoped
  uPlot handle is not reachable from page context, so **series state is
  read from the legend DOM** (`.chart-wrap .u-legend .u-series`, data
  series = rows − 1) and tooltip contents from `.chart-tip` — as the
  skill prescribes.

## Standing note on console errors (ASV only)

The ASV site emits benign **resource 404s** and no JS exceptions:

- `GET /favicon.ico` → 404 (browser auto-request to server root).
- Sparse `graphs/.../<bench>.json` combos → 404. The frontend expands
  the full param cartesian product and requests every combination;
  combos with no data file legitimately 404 (verified: `time_ci_small`
  has exactly one real data file on disk). The chart renders correctly
  from the combos that exist.

Every "no console errors" verdict below means **no JS/runtime errors**;
the only `error`-level console entries in the whole run were these
resource 404s. BMF produced **zero** 404s (complete data).

---

## Checklist items (14, in order)

### 1. Nav tree + param selectors + benchmark-param sub-selection — **agent-verified pass**

- **ASV:** nav leaves are DOM links; clicking a leaf renders the graph.
  On `params_examples.mem_param` the selector groups include the
  benchmark params `number` and `depth` alongside the machine axes.
  Deselecting `number=20` changed the rendered **data series 8 → 4**
  (`number` button `active`→inactive; hash gained `b-0=0&b-1=0&b-1=1`).
  No JS errors.
- **BMF:** 3 nav leaves navigate to graphs; selector groups are
  `branch`, `testbed` (+ `display`); graph renders 1 series. No errors.
- Evidence: `item01-asv-param-subselection.png`.

### 2. Log toggle; date vs. even x-axis — **agent-verified pass**

- **ASV:** clicking `log scale` added `log=1`; clicking `even x-axis`
  added `x=even`. Final toggle state `{log:true, date:false, even:true}`;
  hash tail `…&log=1&x=even`. Only benign 404s in console.
- **BMF:** `log=1` then `x=even` both entered the hash.
- Evidence: `item02-asv-log-even-axis.png`.

### 3. Hover crosshair + tooltip — **agent-verified pass** (DOM contents) · live-Bencher units line **confirm manually** (permanent)

- **ASV** (`params_examples.ParamSuite.track_value`, leftmost point):
  `.chart-tip` = `05d4f83d 2012-12-27` and per-series rows
  `… ('a'): 1 unit`, `('b'): 2 unit`, `('c'): 3 unit` — 8-char hash,
  date, per-series value, **units text "unit"**. Legend "Time" row
  read `2012-12-27 7:06pm`.
- **BMF** (`parse_json (latency)`): `.chart-tip` =
  `e5f6a7b8 2026-01-16` / `value: 11.2 latency` — the **measure slug
  `latency`** surfaces as the units string through the `units || unit`
  path, as specified.
- **Confirm manually (permanent):** the live-Bencher human-readable
  units string (e.g. "nanoseconds (ns)") — no live Bencher project
  exists in the fixtures, so this specific rendering cannot be
  agent-verified.
- Evidence: `item03-asv-tooltip.png`, `item03-bmf-tooltip.png`.

### 4. Commit click-through — **agent-verified pass**

- **ASV:** clicking the leftmost data point opened a new tab at
  `https://github.com/airspeed-velocity/asv/commit/05d4f83d436ce55054016c24b31d959a85b44a1c`
  — the full 40-char hash, prefix matching the tooltip's `05d4f83d`
  (target page is offline; only the URL matters).
- **ASV guards:** a `browser_mouse_drag_xy` drag-zoom opened **no** tab
  (the `sawDrag` guard — confirmed via `browser_tabs list`); a click on
  the **overview strip** opened **no** tab.
- **BMF:** built without `--show-commit-url` (no commit URL in config);
  clicking a data point opened **no** tab — expected.

### 5. Drag-zoom + overview + reset — **agent-verified pass** (with a flagged side-effect)

- **ASV:** main-chart drag → `zoom=…` and narrowed x range; dragging on
  the **overview strip** repositioned the main window
  (`zoom` `1359699392,1374308003` → `1361922433,1370037232`);
  double-click on the main chart removed `zoom=` from the hash.
- **BMF:** drag → `zoom=1768509229.648,1768581568.651`; double-click
  reset removed `zoom=` and — with no commit URL — opened **no** tabs.
- **Finding (side-effect, see item 4):** on the ASV site the
  double-click *reset* also opens commit tabs whenever the two
  constituent clicks land on focused data points (uPlot snaps the
  cursor to the nearest point and the click-through handler fires per
  click). Reset still works, but on a commit-URL site a
  reset-by-double-click can spawn two GitHub tabs. Not observed on BMF
  (no commit URL). Recommend suppressing click-through on the
  reset double-click. Evidence: `item05-asv-zoomed-overview.png`.

### 6. Legend toggle — **agent-verified pass**

- **ASV:** clicking a data-series legend row added `hide=0` and the row
  gained `u-off`; clicking it again removed `hide=` and the series
  restored. (Legend rows shift as the chart re-renders; each click was
  confirmed on the intended row via `elementFromPoint` first.)
- **BMF:** clicking the series row added `hide=0`.
- Evidence: `item06-asv-legend-hidden.png`.

### 7. Toggle-then-selection-change reset — **agent-verified pass**

- **ASV:** hid a series (`hide=1`), then changed an axis selection
  (deselected `numpy=1.8`) → `location.hash` no longer contained
  `hide=` **and** `.u-series.u-off` count = 0.
- **BMF:** hid a series (`hide=0`), then toggled `testbed` → no `hide=`
  in hash, 0 `u-off` rows.

### 8. Pinch-zoom/pan (synthetic) — **confirm manually** (permanent) · app-listener behavior agent-verified

- Synthetic `TouchEvent`s dispatched on `.chart-wrap .u-over`.
- **ASV:** two-finger pinch-out (touchstart → spreading touchmove →
  touchend) committed `zoom=1368842328.406,1374478056.594` on gesture
  end — a narrowed window around the pinch midpoint (cx≈827). A
  subsequent **one-finger pan** shifted the window by an equal delta on
  both ends (`1368842328,1374478056` → `1370211885,1375847613`) — a
  pure pan, width preserved.
- **BMF:** synthetic pinch produced `zoom=1768538025,1768574475` — touch
  listeners are attached here too.
- **Confirm manually (permanent):** native gesture *feel* on a real
  device — synthetic events bypass the browser's gesture recogniser, so
  only the app listeners (not real-device behaviour) are agent-verified.
- Evidence: `item08-09-asv-touch-zoom.png`.

### 9. 2→1 finger transition — **confirm manually** (permanent) · continuity agent-verified

- A continuous synthetic gesture (two fingers → move → lift finger 2 via
  `touchend` with the remaining touch in `touches` → continue one-finger
  move → end) completed with a **finite, correctly-ordered** range
  (`zoom=728643921.406,4034937791.406`, `ordered:true`, `finite:true`)
  and threw no exception — no discontinuous/NaN jump across the lift.
- Note: the app writes `zoom=` only on gesture *end*, not live during
  `touchmove`, so mid-gesture range sampling via the hash is not
  possible; continuity was asserted on the committed end state.
- **Confirm manually (permanent):** same real-device residual as item 8.

### 10. Grid lazy thumbnails + list sorting + no dead columns — list half **agent-verified pass** · lazy-thumbnail half **confirm manually**

- **List sorting / columns — agent-verified pass:**
  - Headers are **exactly** `Benchmark / Last value / Error` (no dead
    columns) on both sites.
  - **ASV** "Last value": ascending = `0.0101, 1, 3, 3, 4, 520, 776,
    1040, 1552` (numeric, not lexicographic — "1040" sorts after "776");
    descending = the exact reverse. "Benchmark" sorts alphabetically.
    "Error" ascending places the one non-null (`0.8 seconds`) first and
    all nulls last (**nulls-last** confirmed).
  - **BMF** "Last value" ascending = `7.2, 10.1, 1250` (numeric across
    mixed `latency`/`throughput` units).
- **Grid lazy thumbnails — confirm manually (fixtures too small):** the
  grid is the landing view and renders every thumbnail canvas. The lazy
  mechanism **is** implemented — `src/ulv/outputs/html_uplot/static/js/views/grid.js`
  uses an `IntersectionObserver` with `rootMargin: "200px"`. But both
  fixtures have ≤4 benchmarks; even forced into a 400×300 viewport the
  stacked cards sit ~107px apart, inside the 200px preload margin, so
  all canvases mount immediately and mount-on-scroll cannot be
  exercised. Needs a fixture with enough benchmarks to push a card
  beyond the 200px margin.
- Evidence: `item10-asv-list-sort.png`, `item10-bmf-list-sort.png`.

### 11. Hash round-trip — **agent-verified pass**

- **ASV:** composed a full state via UI —
  `benchmark=track_value` + param deselection (`numpy` set) + `hide=0`
  + `log=1` + `x=even` + `zoom=0.598,1.4`. Opened the resulting URL in a
  **fresh tab**: `location.hash` was **byte-for-byte equal** to the
  composed hash, with 1 `u-off` row, `{log:true, even:true, date:false}`,
  and `zoom=` present.
- **BMF:** navigating to a hand-composed full-state URL
  (`…&hide=0&log=1&x=even&zoom=0.2,0.85`) restored it with the hash
  unchanged (stable serialisation), 1 hidden row, log+even active.
- Evidence: `item11-asv-roundtrip-restored.png`.

### 12. Phone-width viewport — **agent-verified pass** (with a flagged edge-case bug)

- At **375×700**, page chrome does not overflow and the nav stacks
  above content:
  - **ASV grid** (fresh load): `scrollWidth == innerWidth == 375`,
    `navStacksAbove:true`, no overflowing elements.
  - **ASV graph** (fresh load): `scrollWidth == innerWidth == 375`; the
    chart reflows to fit (`.chart-wrap` 343px).
  - Live desktop→phone resize (unzoomed) reflows correctly (375, no
    overflow). **BMF** graph fresh-load: 375, nav stacks.
- **Finding (agent-verified edge-case bug):** with an **active zoom**, a
  live viewport resize to 375px leaves the **overview strip** (the
  second uPlot) at its previous width (`.u-over` 926px) while the main
  chart reflows (238px), producing page-level horizontal overflow
  (`documentElement.scrollWidth = 943 > 375`) until re-navigation. On a
  fresh phone load the strip is sized correctly, so a real phone is
  unaffected unless the user resizes/rotates while zoomed. Recommend the
  overview strip re-fit on window resize.
- Evidence: `item12-asv-phone-grid.png`, `item12-asv-phone-graph-overflow.png`,
  `item12-asv-phone-overview-overflow-when-zoomed.png`,
  `item12-bmf-phone-graph.png`.

### 13. Machine axis presence — **agent-verified pass**

- **ASV** selector-group legends:
  `Cython, arch, branch, cpu, env-ULV_TEST, lapack, machine, numpy, os,
  python, ram, …` — `machine` appears as an ordinary axis group.
- **BMF** selector-group legends: `branch, testbed, display` — **no
  `machine` group anywhere** (`hasMachine:false`).
- Evidence: `item13-bmf-no-machine-axis.png`.

### 14. Network isolation — **agent-verified pass**

Every app request stays on the site's own origin; no external hosts.
The deliberate `github.com/.../commit/...` tabs from items 4–5 are
user-initiated top-level navigations to the configured commit URL, not
app resource requests. `favicon.ico` is a benign browser request to the
server root (same host).

**ASV** (`http://127.0.0.1:8123/asv-site/…`), verbatim:

```
1. [GET] http://127.0.0.1:8123/asv-site/ => [200] OK
2. [GET] http://127.0.0.1:8123/asv-site/vendor/uPlot.min.css => [200] OK
3. [GET] http://127.0.0.1:8123/asv-site/app.css => [200] OK
4. [GET] http://127.0.0.1:8123/asv-site/vendor/uPlot.iife.min.js => [200] OK
5. [GET] http://127.0.0.1:8123/asv-site/js/main.js => [200] OK
6. [GET] http://127.0.0.1:8123/asv-site/js/nav.js => [200] OK
7. [GET] http://127.0.0.1:8123/asv-site/js/state.js => [200] OK
8. [GET] http://127.0.0.1:8123/asv-site/js/views/graph.js => [200] OK
9. [GET] http://127.0.0.1:8123/asv-site/js/views/grid.js => [200] OK
10. [GET] http://127.0.0.1:8123/asv-site/js/views/list.js => [200] OK
11. [GET] http://127.0.0.1:8123/asv-site/js/data.js => [200] OK
12. [GET] http://127.0.0.1:8123/asv-site/js/touch.js => [200] OK
13. [GET] http://127.0.0.1:8123/asv-site/js/views/overview.js => [200] OK
14. [GET] http://127.0.0.1:8123/asv-site/info.json => [200] OK
15. [GET] http://127.0.0.1:8123/asv-site/index.json => [200] OK
16. [GET] http://127.0.0.1:8123/asv-site/graphs/summary/params_examples.ParamSuite.track_value.json => [200] OK
17. [GET] http://127.0.0.1:8123/asv-site/graphs/summary/params_examples.mem_param.json => [200] OK
18. [GET] http://127.0.0.1:8123/asv-site/graphs/summary/time_ci_small.json => [200] OK
19. [GET] http://127.0.0.1:8123/asv-site/graphs/summary/time_units.time_unit_parse.json => [200] OK
20. [GET] http://127.0.0.1:8123/asv-site/graphs/Cython-null/arch-x86_64/branch/cpu-Intel(R)%20Core(TM)%20i5-2520M%20CPU%20%40%202.50GHz%20(4%20cores)/env-ULV_TEST-null/lapack-null/machine-cheetah/numpy-1.8/os-Linux%20(Fedora%2020)/python-2.7/ram-8.2G/params_examples.ParamSuite.track_value.json => [200] OK
21. [GET] http://127.0.0.1:8123/asv-site/graphs/Cython/arch-aarch64/branch/cpu-Apple%20M1%20(8%20cores)/env-ULV_TEST-null/lapack-null/machine-leopard/numpy-1.8/os-macOS%2014.2/python-2.7/ram-16GB/params_examples.ParamSuite.track_value.json => [200] OK
22. [GET] http://127.0.0.1:8123/asv-site/graphs/Cython-null/arch-x86_64/branch/cpu-Intel(R)%20Core(TM)%20i5-2520M%20CPU%20%40%202.50GHz%20(4%20cores)/env-ULV_TEST-1/lapack/machine-cheetah/numpy-1.9/os-Linux%20(Fedora%2020)/python-2.7/ram-8.2G/params_examples.ParamSuite.track_value.json => [404] File not found
23. [GET] http://127.0.0.1:8123/asv-site/graphs/Cython-null/arch-x86_64/branch/cpu-Intel(R)%20Core(TM)%20i5-2520M%20CPU%20%40%202.50GHz%20(4%20cores)/env-ULV_TEST-null/lapack-null/machine-cheetah/numpy-1.8/os-Linux%20(Fedora%2020)/python-2.7/ram-8.2G/summary.json => [200] OK
24. [GET] http://127.0.0.1:8123/asv-site/graphs/summary/params_examples.ParamSuite.track_value.json => [200] OK
25. [GET] http://127.0.0.1:8123/asv-site/graphs/summary/params_examples.mem_param.json => [200] OK
26. [GET] http://127.0.0.1:8123/asv-site/graphs/summary/time_ci_small.json => [200] OK
27. [GET] http://127.0.0.1:8123/asv-site/graphs/summary/time_units.time_unit_parse.json => [200] OK
```

(#22 is one of the expected sparse-combo 404s; same host.)

**BMF** (`http://127.0.0.1:8123/bmf-site/…`), verbatim:

```
1. [GET] http://127.0.0.1:8123/bmf-site/ => [200] OK
2. [GET] http://127.0.0.1:8123/bmf-site/vendor/uPlot.min.css => [200] OK
3. [GET] http://127.0.0.1:8123/bmf-site/app.css => [200] OK
4. [GET] http://127.0.0.1:8123/bmf-site/vendor/uPlot.iife.min.js => [200] OK
5. [GET] http://127.0.0.1:8123/bmf-site/js/main.js => [200] OK
6. [GET] http://127.0.0.1:8123/bmf-site/js/nav.js => [200] OK
7. [GET] http://127.0.0.1:8123/bmf-site/js/state.js => [200] OK
8. [GET] http://127.0.0.1:8123/bmf-site/js/views/graph.js => [200] OK
9. [GET] http://127.0.0.1:8123/bmf-site/js/views/grid.js => [200] OK
10. [GET] http://127.0.0.1:8123/bmf-site/js/views/list.js => [200] OK
11. [GET] http://127.0.0.1:8123/bmf-site/js/data.js => [200] OK
12. [GET] http://127.0.0.1:8123/bmf-site/js/touch.js => [200] OK
13. [GET] http://127.0.0.1:8123/bmf-site/js/views/overview.js => [200] OK
14. [GET] http://127.0.0.1:8123/bmf-site/info.json => [200] OK
15. [GET] http://127.0.0.1:8123/bmf-site/index.json => [200] OK
16. [GET] http://127.0.0.1:8123/bmf-site/graphs/summary/parse_json%20(latency).json => [200] OK
17. [GET] http://127.0.0.1:8123/bmf-site/graphs/summary/parse_json%20(throughput).json => [200] OK
18. [GET] http://127.0.0.1:8123/bmf-site/graphs/summary/serialize_json%20(latency).json => [200] OK
19. [GET] http://127.0.0.1:8123/bmf-site/graphs/branch/testbed-linux-x64/parse_json%20(latency).json => [200] OK
20. [GET] http://127.0.0.1:8123/bmf-site/graphs/branch/testbed-linux-x64/summary.json => [200] OK
21. [GET] http://127.0.0.1:8123/bmf-site/graphs/summary/parse_json%20(latency).json => [200] OK
22. [GET] http://127.0.0.1:8123/bmf-site/graphs/summary/parse_json%20(throughput).json => [200] OK
23. [GET] http://127.0.0.1:8123/bmf-site/graphs/summary/serialize_json%20(latency).json => [200] OK
```

---

## Summary

| # | Item | Verdict |
|---|------|---------|
| 1 | Nav tree + param selectors + sub-selection | agent-verified pass |
| 2 | Log toggle; date vs. even x-axis | agent-verified pass |
| 3 | Hover crosshair + tooltip | agent-verified pass · live-Bencher units **confirm manually** |
| 4 | Commit click-through | agent-verified pass |
| 5 | Drag-zoom + overview + reset | agent-verified pass (reset-double-click tab side-effect flagged) |
| 6 | Legend toggle | agent-verified pass |
| 7 | Toggle-then-selection-change reset | agent-verified pass |
| 8 | Pinch-zoom/pan (synthetic) | **confirm manually** (real-device feel); listeners agent-verified |
| 9 | 2→1 finger transition | **confirm manually** (real-device feel); continuity agent-verified |
| 10 | Grid lazy thumbnails + list sorting + columns | list/columns agent-verified pass · lazy thumbnails **confirm manually** (fixtures too small) |
| 11 | Hash round-trip | agent-verified pass |
| 12 | Phone-width viewport | agent-verified pass (overview-strip resize-while-zoomed overflow flagged) |
| 13 | Machine axis presence | agent-verified pass |
| 14 | Network isolation | agent-verified pass |

### Follow-ups surfaced — all resolved 2026-07-19

1. **Reset double-click opens commit tabs (item 5, commit-URL sites)** —
   **fixed.** The point-click commit-open is now debounced (250 ms) and
   cancelled by the trailing `dblclick`, so a single click still opens
   exactly one tab while a zoom reset opens none. Re-verified in-browser
   (`fix-verify-item12-*` evidence set; single click → 1 tab, reset →
   0 tabs). Static guard: `test_point_click_commit_open_is_double_click_cancellable`.
2. **Overview strip doesn't re-fit on resize while zoomed (item 12)** —
   **fixed.** The window resize handler now re-fits the overview strip as
   well as the main chart and repaints the zoom window. The zoom-then-
   resize-to-375 repro that previously gave `scrollWidth 943` now gives
   `375` (no overflow); overview `.u-over` reflows 926 → 341 px. Static
   guard: `test_resize_refits_overview_not_just_main_chart`.
3. **Lazy-grid coverage gap (item 10)** — **guarded.** No fixture is
   large enough to push a thumbnail past the 200 px `rootMargin`, so
   runtime mount-on-scroll stays a manual check; a static wiring guard
   (`test_grid_view_mounts_thumbnails_lazily`) now protects the
   `IntersectionObserver` mechanism against regression. A larger grid
   fixture remains the way to exercise it in-browser if desired.

Checklist boxes in `tasks.md` are intentionally left unticked — ticking
is the owner's act at sign-off. Annotate against this report.
