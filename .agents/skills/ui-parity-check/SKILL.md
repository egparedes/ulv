---
name: ui-parity-check
description: |
  Run the automated browser UI parity check for the html-uplot frontend.
  Use this skill whenever the user says "run the UI parity check",
  "parity checklist", "frontend regression check", "check the frontend in
  a browser", or after ANY change to src/ulv/outputs/html_uplot/static/.
  Drives all 14 browser-interactive checklist items against both fixture
  sites via the playwright MCP server and writes a per-item evidence
  report with three-way verdicts for human sign-off review.
---

# ui-parity-check

Automates the "Manual parity checklist" of a frontend feature spec
(first target: `development/work/2026-07-uplot-frontend/tasks.md`). Takes one
parameter: the **target spec dir** the report belongs to (default
`development/work/2026-07-uplot-frontend/`).

## Prerequisites — check before doing anything else

1. **The `playwright` MCP server must be loaded in THIS session.**
   Check by listing its tools (they are prefixed `browser_`). If they
   are absent, STOP and tell the user to restart the session — under
   Claude Code they must also approve the server when prompted (it
   reads `.mcp.json`); OpenCode enables it via `.opencode/opencode.jsonc`
   with no separate approval step. Do not work around a missing
   server. See ADR 0009.
2. Browser binary: both configs pin `--browser chromium` (the server
   default would be chrome-for-testing), so if navigation fails with a
   missing-browser error, the user must run `npx playwright install
   chromium` once. Never run installs from `make verify`.
3. Never use `browser_run_code_unsafe` (ADR 0009); page-context
   `browser_evaluate` only.

## Setup

Build both fixture sites and serve them from a **subdirectory** (the
commands are the checklist preamble's, verbatim; run from the repo
root):

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

Sites: `http://127.0.0.1:8123/asv-site/` (machine axes) and
`http://127.0.0.1:8123/bmf-site/` (machine-less). Run every item on
**both sites unless the item names one**. Create
`development/work/<target>/parity-evidence/` (gitignored) for screenshots before
starting.

## Calibration — mandatory before any verdict

Confirm coordinate semantics empirically at the start of every run:
`browser_evaluate` `getBoundingClientRect()` on a known clickable
element, `browser_mouse_click_xy` at its center, and verify the click
landed (DOM/hash effect). Also sanity-check `browser_mouse_drag_xy`
produces a drag-select on the main chart and `clickCount: 2` performs
a double-click. If clicks land offset, stop and diagnose before
recording any verdict.

Chart-point coordinates: `browser_evaluate`
`document.querySelector('.chart-wrap .u-over').getBoundingClientRect()`
and derive point positions from the plotted x range; the tooltip's
reported hash confirms which revision a position hits.

## Per-item procedures (14 items, checklist order)

1. **Nav tree + param selectors + benchmark-param sub-selection** —
   `browser_navigate` to each site; nav/selectors are DOM (not
   canvas), so use `browser_click` with a11y refs. Click a nav leaf →
   graph renders. On the ASV site open `params_examples.mem_param`:
   number/depth selector groups appear; toggling a value changes the
   rendered series count. No uPlot instance is reachable from page
   context (the chart handle is module-scoped, not on `window`) —
   read series state from the legend DOM uPlot renders instead:
   `browser_evaluate` counting `.chart-wrap .u-legend .u-series` rows
   (the legend includes one row for the x series, so data series =
   rows − 1). Screenshot. Pass: selections filter series with no
   console errors.
2. **Log toggle; date vs. even x-axis** — `browser_click` the "log
   scale", "date x-axis", "even x-axis" buttons;
   `browser_console_messages` must show no errors; `location.hash`
   gains `log=1` / `x=even`; before/after screenshots. Pass: axis
   rendering changes and hash reflects each toggle.
3. **Hover crosshair + tooltip** — compute a data-point position (see
   Calibration), `browser_mouse_move_xy` onto it, read the tooltip DOM
   via `browser_evaluate` (`.chart-tip` innerText): 8-char hash, date,
   per-series value, units text. BMF shows the measure slug (e.g.
   `latency`) through the same `units || unit` path — agent-verified.
   The live-Bencher human-readable units string ("nanoseconds (ns)")
   is **confirm manually** — no live Bencher project in fixtures.
   Screenshot with tooltip visible.
4. **Commit click-through** — `browser_mouse_click_xy` on a data
   point (ASV site); a new tab opens on
   `https://github.com/airspeed-velocity/asv/commit/<full hash>`
   (verify the URL via the tab list; the page itself may be offline —
   only the URL matters). Then: finish a `browser_mouse_drag_xy`
   drag-zoom and assert NO new tab opened; click a point on the
   overview strip and assert NO new tab opened. Pass: exactly the
   first action opens a tab.
5. **Drag-zoom + overview + reset** — `browser_mouse_drag_xy` across
   part of the main chart: `zoom=` appears in `location.hash` and the
   x range narrows; drag on the overview strip: main chart zooms and
   the strip paints the window; `browser_mouse_click_xy` with
   `clickCount: 2` on the main chart: `zoom=` leaves the hash.
   Screenshots at each stage.
6. **Legend toggle** — `browser_click` a legend series label:
   series hides, `hide=` appears in the hash; click again to restore.
   Screenshot.
7. **Toggle-then-selection-change reset** — hide a series, then
   change an axis selection (or switch benchmark): `browser_evaluate`
   that `location.hash` no longer contains `hide=` (authoritative —
   the app writes `hidden: []` on every selection change) AND that no
   legend row carries the hidden-series class:
   `document.querySelectorAll('.chart-wrap .u-legend .u-series.u-off').length === 0`.
8. **Pinch-zoom/pan (synthetic)** — `browser_evaluate` dispatching
   synthetic `TouchEvent`s on `.chart-wrap .u-over`: touchstart with
   two touches, touchmove spreading them (pinch), touchend; then a
   one-finger pan sequence. Pass: x range changes around the pinch
   midpoint and the final range lands in `zoom=` on gesture end.
   Verdict cap: app-listener behavior is agent-verifiable; native
   gesture *feel* on a real device is **confirm manually** (synthetic
   events bypass browser gesture recognition — state this reason).
9. **2→1 finger transition** — same technique: start two-finger,
   lift one mid-gesture, continue moving; `browser_evaluate` the x
   range across the transition — no discontinuous jump. Same
   real-device residual as item 8.
10. **Grid lazy thumbnails + list sorting + no dead columns** — grid
    is the landing view; count mounted thumbnail canvases, scroll
    (`browser_press_key` End / `browser_evaluate` scrollTo), count
    again — it grows (laziness). Switch to List; `browser_click` each
    sort header asc/desc and `browser_evaluate` the column values are
    ordered (numbers numerically, nulls last); headers are exactly
    Benchmark / Last value / Error. Screenshots of both views.
11. **Hash round-trip** — compose a state: benchmark + a param
    deselection + log + even x + zoom + one hidden series; read
    `location.hash`; `browser_navigate` to the full URL in a fresh
    tab; `browser_evaluate` the restored state equals the composed one
    (hash string equality plus visible-series/toggle spot checks).
    Screenshots of both tabs.
12. **Phone-width viewport** — `browser_resize` to 375×700;
    `browser_evaluate`
    `document.documentElement.scrollWidth <= window.innerWidth`; nav
    stacks above content. Screenshot. Pass: no horizontal overflow of
    page chrome.
13. **Machine axis presence** — `browser_evaluate` the selector group
    legends: BMF site has no `machine` group anywhere; ASV site shows
    `machine` as an ordinary axis group among the others.
14. **Network isolation** — after browsing all three views on a site,
    `browser_network_requests`: every URL starts with
    `http://127.0.0.1:8123/asv-site/` (resp. `/bmf-site/`); no other
    hosts. Paste the full listing verbatim into the report.

## Report contract

- Path: `development/work/<target-feature>/parity-report-<YYYY-MM-DD>.md`
  (committed). Screenshots: `development/work/<target-feature>/parity-evidence/`
  (gitignored), referenced by filename per item.
- Preamble: date, harness + server version, sites built, calibration
  result.
- Exactly 14 items, one-to-one with the checklist **in order**. Every
  verdict is one of: **agent-verified pass** / **agent-verified
  fail** / **confirm manually** — verbatim, no other vocabulary.
- Each item carries inline textual evidence (observed hash strings,
  DOM state, console output; item 14 the verbatim request listing) so
  the report stands alone without the screenshots.
- Items 3 (live-Bencher units) and 8/9 (real-device touch feel) are
  permanently **confirm manually** with their stated reasons. Anything
  flaky or unverifiable in a given run is likewise **confirm
  manually** with a reason — never silently passed.
- Do NOT tick the target checklist's boxes; annotate items with the
  verdict + report reference. Ticking is the owner's act at sign-off.

## Gotchas

- TODO(first run): confirm the coordinate semantics of the `*_xy`
  tools empirically (expected: viewport-level CSS px, matching
  `getBoundingClientRect`; alternatives would be device px or
  chrome-offset coords). Replace this TODO with the confirmed
  semantics after the first calibrated run.
- Keep devtools-equivalent caching disabled: the server's `--isolated`
  profile starts cold, but re-runs within one session can hit the
  HTTP cache — a cached JS file once masked a frontend fix. When in
  doubt, `browser_navigate` with a cache-busting query string on
  `index.html` only (never on data files under test).
- The `python3 -m http.server` process must be started in the
  background and killed at the end of the run; check the port is free
  first (`8123`).
- uPlot's drag-zoom applies before the DOM click event; the app
  guards click-through with a `sawDrag` flag — item 4's
  no-tab-after-drag assertion is exactly that guard's regression test.
