# Automated Browser-Interactive UI Parity Checks for the uPlot Frontend

## Problem

The completed `html-uplot` frontend feature
(`specs/2026-07-uplot-frontend/`) ends with a "Manual parity checklist —
HUMAN PASS REQUIRED": 14 browser-interactive items (canvas drag-zoom,
hover tooltips, legend toggling, URL-hash round-trip, touch pinch/pan,
phone-width viewport, network isolation, and more) at the bottom of that
feature's `tasks.md`. They block feature sign-off because they exercise
real user input against a `<canvas>`-based UI that agents could not
drive, so a human must spend a careful, error-prone session clicking
through two fixture sites with devtools open. Worse, the cost recurs:
these same checks are the regression safety net for *every* future
frontend change, so each frontend touch re-imposes a full manual pass —
or, more likely, the pass quietly gets skipped.

## Goal

An agent can run the browser-interactive parity checklist end to end
against the generated fixture sites and produce a recorded per-item
evidence report, shrinking the blocking human step from a full manual
pass to a short review of the report plus the few explicitly flagged
items that still need human confirmation.

## Users & stakeholders

- **The project owner (sign-off authority)**, whose blocking manual
  pass shrinks to reviewing a recorded evidence report and spot-checking
  the flagged residual items.
- **ulv's developers/agents**, who gain a repeatable, on-demand
  regression check for any future frontend change instead of a
  one-shot human ritual.
- **Users of both agent harnesses (Claude Code and OpenCode)**, since
  the repo's convention is single-definition tooling shared across
  both; the capability must be available in either.
- **Future contributors touching the frontend**, who inherit a
  documented, invocable check rather than tribal knowledge in an old
  tasks file.
- **Sign-off:** the project owner (repository owner).

## Background research

Verified against primary sources on 2026-07-19 (cite; do not
re-litigate): **Playwright MCP** (`@playwright/mcp`, Microsoft,
Apache-2.0, v0.0.78 of 2026-07-09, actively maintained, Node 18+, runs
locally via npx, fully offline after a one-time browser install) is the
selected browser-automation server. The decisive capability is
`--caps=vision`, which adds coordinate-based mouse tools
(`browser_mouse_drag_xy`, `browser_mouse_click_xy` with clickCount) —
required because uPlot charts are `<canvas>` elements with no
accessibility-tree entries, so snapshot-based element targeting cannot
reach data points. The server also provides hover, keyboard, viewport
resize, screenshots, console-message capture, network-request listing,
and page-context JS evaluation (`browser_evaluate`), the last of which
can dispatch synthetic TouchEvent objects for pinch/pan — exercising
the app's own DOM listeners, but *not* native browser gesture
recognition. Rejected alternatives: chrome-devtools-mcp (no coordinate
drag tool), Puppeteer MCP (archived), Selenium MCP (dormant since
Feb 2025), cloud browser services (violate the fully-local constraint).
Config mechanisms confirmed current: Claude Code project scope is
`.mcp.json` at the repo root (user approval prompt on first use);
OpenCode is the `"mcp"` key in `.opencode/opencode.jsonc`; the repo's
harness pattern is a single definition shared across both (see
`docs/harness-usage.md`).

## Success criteria

- The browser-automation MCP server is configured for both harnesses
  (Claude Code and OpenCode) — verified by starting a fresh session in
  each harness and listing the server's tools successfully.
- A harness skill exists that, when invoked, builds both fixture sites
  (the ASV fixture with machine axes and the machine-less BMF fixture),
  serves them from a subdirectory, and drives every item of the
  14-item manual parity checklist from
  `specs/2026-07-uplot-frontend/tasks.md` — verified by invoking the
  skill and observing it complete without manual intervention.
- Invoking the skill produces a recorded evidence report containing a
  verdict for each of the 14 checklist items, with screenshot evidence
  attached per item — verified by inspecting the report after a run
  and matching its items one-to-one against the checklist.
- Every report verdict is one of "agent-verified pass",
  "agent-verified fail", or "confirm manually"; the two
  reduced-not-eliminated items (real-device touch gesture feel;
  live-Bencher human-readable units string) and any item the agent
  could not reliably verify are marked "confirm manually" with a stated
  reason, never silently passed — verified by inspecting the report's
  verdicts for those items.
- The network-isolation checklist item is verified from recorded
  request evidence: the report shows that browsing all views fetched
  only the sites' own static files and no external hosts — verified by
  inspecting the report's request listing for that item.
- `make verify` behavior is unchanged: no new gate steps, and no
  browser, agent, network, or MCP dependency is required to run it —
  verified by running `make verify` before and after the change and
  confirming identical steps and no new prerequisites.
- No new Python or runtime dependency is added to the package —
  verified by diffing the project's dependency declarations before and
  after.
- The MCP-server choice is recorded as a new ADR (next free number in
  `docs/adr/`, currently 0009) and `docs/harness-usage.md` documents
  how to approve the server and invoke the skill — verified by the
  presence and content of both documents.
- A first recorded run against the uplot feature's checklist exists,
  with its report and screenshots available for the project owner's
  sign-off review — verified by the presence of that report and the
  owner being able to review it. Operational constraint, recorded here
  rather than hidden: this run must happen in a session where the MCP
  server is loaded and user-approved, so it cannot be produced by the
  deterministic gate or an unattended process.

## Non-goals

- **No pytest-playwright or CI browser tests.** Wiring browser
  automation into the deterministic test suite or CI is a separate
  future decision.
- **No visual-regression pixel diffing.** Screenshots are evidence for
  human review, not baselines to compare against.
- **No changes to the frontend code itself.** The `html-uplot`
  generator and its assets are exercised, not modified; if a check
  finds a bug, fixing it is separate work.
- **Not a replacement for the deterministic e2e crawl tests.** Those
  remain the automated gate; this is a recorded agent-executed check
  layered on top.
- **No cloud or remote browser services.** Everything runs locally and
  offline after the one-time browser install.
- **No elimination of human sign-off.** The human pass is reduced to a
  short review, not removed; the two residual items stay human-owned.

## Decisions

1. **Server: Playwright MCP, version-pinned** (not `@latest`), run
   headless with the `--isolated` in-memory profile and `--caps=vision`
   for coordinate-based canvas interaction; the browser binary is
   pre-installed once (or system Chrome is used). Rationale: the
   verified research verdict above — it is the only maintained,
   fully-local option with coordinate drag tools.
2. **The automation lives as a harness skill** (under
   `.agents/skills/`, symlinked into both harnesses) encoding the full
   workflow: build both fixture sites (ASV + machine-less BMF) → serve
   them from a subdirectory → drive every checklist item → write a
   recorded per-item evidence report (verdict + screenshots) for human
   review and sign-off.
3. **`make verify` stays untouched.** The deterministic gate gains no
   browser, agent, or network dependency. This is an agent-executed
   recorded check, not a CI test.
4. **No new Python/runtime dependency.** The MCP server is harness
   tooling, outside the package's dependency tree. A short ADR (next
   free number in `docs/adr/`) records the choice.
5. **The `browser_run_code_unsafe` tool capability is not used.**
   Page-context `browser_evaluate` only.
6. **Automation scope: 12 of the 14 checklist items become fully
   agent-runnable; two are reduced, not eliminated** — real-device
   touch gesture feel (synthetic TouchEvents exercise the app's
   listeners, not native gesture recognition) and the live-Bencher
   human-readable units string (no live Bencher project in fixtures).
   The report must say so explicitly: flaky or unverifiable items are
   reported as "confirm manually", never silently passed.
7. **Both harnesses get the server config** (Claude Code and
   OpenCode), following the repo's single-definition-shared pattern.

## Open questions

- None blocking. One flag for the Architect: the report's format and
  storage location (and whether screenshots are committed or
  gitignored) are implementation choices, but the binding requirements
  are the three-way verdict vocabulary, per-item screenshot evidence,
  and reviewability by the project owner.
