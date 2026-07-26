# 9. Playwright MCP as the browser-automation server for UI parity checks

## Status

Accepted

## Context

The `html-uplot` frontend (ADR 0008) ships with a 14-item
browser-interactive parity checklist that previously required a full
manual pass: canvas drag-zoom, hover tooltips, legend toggling,
URL-hash round-trips, synthetic touch gestures, viewport checks, and
network-isolation evidence. Those checks recur for every future
frontend change, so they need to be agent-drivable.

uPlot charts are `<canvas>` elements with no accessibility-tree
entries, so snapshot-based element targeting cannot reach data
points — the automation server must offer coordinate-based mouse
tools. Research verified against primary sources on 2026-07-19
(recorded in `development/work/2026-07-ui-parity-automation/spec.md`; do not
re-litigate): **Playwright MCP** (`@playwright/mcp`, Microsoft,
Apache-2.0, v0.0.78 of 2026-07-09, actively maintained, Node 18+) is
the only maintained, fully-local option with coordinate mouse tools —
`--caps=vision` adds `browser_mouse_drag_xy` and
`browser_mouse_click_xy` (with clickCount), alongside hover, keyboard,
viewport resize, screenshots, console capture, network-request
listing, and page-context `browser_evaluate` (which can dispatch
synthetic TouchEvents). Rejected alternatives:

- **chrome-devtools-mcp** — no coordinate drag tool, so canvas
  drag-zoom cannot be exercised.
- **Puppeteer MCP** — archived upstream.
- **Selenium MCP** — dormant since Feb 2025.
- **Cloud browser services** — violate the fully-local constraint.

## Decision

- Configure `@playwright/mcp`, **pinned to 0.0.78** (never `@latest`),
  for both harnesses: `.mcp.json` at the repo root (Claude Code
  project scope) and the `"mcp"` key in `.opencode/opencode.jsonc`
  (OpenCode). Two files because the config formats differ — the one
  place the single-definition-shared pattern cannot be a symlink — so
  `tests/test_harness_config.py` pins the identical version string in
  both to prevent drift.
- Run flags: `--headless --isolated --caps=vision --browser chromium`.
  `--isolated` keeps the browser profile in memory (no state leaks
  between runs); `--caps=vision` provides the coordinate mouse tools;
  `--browser chromium` pins the Playwright-bundled chromium (the server
  default is chrome-for-testing) so the `npx playwright install
  chromium` setup step matches what the server launches.
- **`browser_run_code_unsafe` is never used.** Page-context
  `browser_evaluate` only (spec Decision 5).
- Update policy: manual bump — edit both configs and the test
  constant in one commit, re-verifying against the upstream release.
- Browser binary: one-time `npx playwright install chromium` (or
  system Chrome via `--browser chrome`), performed by the user, never
  by `make verify`. Note: the first `npx` use fetches the pinned
  package itself (network once, then cached); fully local and offline
  thereafter.
- This is harness tooling only: no Python or runtime dependency is
  added to the package, and `make verify` gains no step and no
  browser/network/MCP prerequisite.

## Consequences

- Agents can drive the full parity checklist (the `ui-parity-check`
  skill) and produce recorded evidence reports, shrinking the human
  pass to reviewing the report plus the flagged residuals.
- An MCP server only loads in sessions started after its config
  exists and the user approves it, so recorded runs cannot come from
  the deterministic gate or unattended processes — a recorded
  operational constraint, not a bug.
- Two config files must stay in lockstep; the deterministic guard
  makes drift a test failure instead of a silent skew.
- Version pinning means no silent upstream changes, at the cost of a
  manual bump ritual (documented above).
- Synthetic TouchEvents exercise the app's own listeners but not
  native browser gesture recognition, so real-device touch feel stays
  a human check forever (spec Decision 6).
