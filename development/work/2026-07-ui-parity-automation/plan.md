# Plan

Implements `spec.md` (approved, incl. its 7 Decisions). Reference
material: the workload being automated is the 14-item "Manual parity
checklist — HUMAN PASS REQUIRED" at the bottom of
`specs/2026-07-uplot-frontend/tasks.md` (its preamble records the
verbatim fixture build/serve commands); harness wiring conventions in
`docs/harness-usage.md`; the house skill example in
`.agents/skills/verify/SKILL.md`; vendoring/ADR precedent in
`docs/adr/0008-vendor-uplot-for-self-authored-frontend.md`.

Server facts were verified against primary sources on 2026-07-19 (see
`spec.md` Background research); the plan builds on them and does not
re-research.

**Phasing constraint (from the spec, drives the whole plan):** an MCP
server only becomes available in a session started *after* its config
exists and the user has approved it. So Phase 1 lands everything
verifiable without a live server (config, ADR, skill, docs, guards),
and Phase 2 — the first recorded run plus the empirical confirmations —
executes in a *fresh, server-approved session*. Phase 2's steps and
exit criteria are written to be executable standalone by a future
session with no memory of this one.

## Architecture decisions

- **Browser-automation server**: `@playwright/mcp`, **pinned to
  0.0.78** (never `@latest`), run `--headless --isolated
  --caps=vision --browser chromium`; `browser_run_code_unsafe` is never used
  (page-context `browser_evaluate` only, spec Decision 5); browser
  binary via one-time `npx playwright install chromium` (or system
  Chrome with `--browser chrome`), never installed by `make verify`.
  ADR needed: 0009 — Playwright MCP as the browser-automation server
  (records the choice, rejected alternatives, pin/update policy, and
  the no-unsafe-eval rule; authored in Phase 1 before the config
  lands).
- **Dual-harness config, kept in lockstep**: Claude Code gets
  `.mcp.json` at the repo root; OpenCode gets an `"mcp"` key in the
  existing `.opencode/opencode.jsonc` — two files because the harness
  config formats differ (this is the one place the single-definition
  pattern can't be a symlink), so a deterministic test pins the exact
  version string in both to prevent drift. ADR: covered by 0009.
- **The workflow is one skill**: `.agents/skills/ui-parity-check/`
  (house SKILL.md format, name + trigger description frontmatter),
  visible to both harnesses through the existing `.claude/skills/` /
  `.opencode/skills/` symlink layout — no new wiring expected; Phase 1
  confirms the layout and only adds symlinks if it turns out to be
  per-skill rather than directory-level. ADR: n/a.
- **Report location — the spec dir of the feature under check**: the
  first run's report is committed as
  `specs/2026-07-uplot-frontend/parity-report-<YYYY-MM-DD>.md` (dated,
  since runs recur). Rationale: the report is the evidence that
  discharges *that* feature's blocking checklist, and sign-off review
  happens where the checklist lives; the skill takes the target spec
  dir as its one invocation parameter so future frontend features get
  reports in their own dirs. ADR: n/a.
- **Report format is fixed**: exactly 14 items, one-to-one with the
  checklist in order; every verdict is one of **agent-verified pass /
  agent-verified fail / confirm manually** (binding vocabulary, spec
  Decision 6); each item carries textual evidence inline (observed
  hash strings, DOM state read via `browser_evaluate`, and — for the
  network-isolation item — the recorded request listing) so the
  committed report stands alone without the screenshots; screenshot
  filenames are referenced per item. The two permanent residuals
  (real-device touch feel; live-Bencher units string) are always
  "confirm manually" with a stated reason. ADR: n/a.
- **Screenshots gitignored, report committed**: screenshots go to
  `specs/<feature>/parity-evidence/`, ignored via one root
  `.gitignore` line (`specs/*/parity-evidence/`). Rationale: recurring
  multi-MB binary artifacts would bloat the repo forever (house
  convention already gitignores per-spec scratch); the owner reviews
  them locally in the session where the run happened, and the
  committed report is textually self-sufficient. ADR: n/a.
- **Cheap deterministic guards, no new gate steps**: one stdlib-only
  test module (`tests/test_harness_config.py`) asserts `.mcp.json`
  parses as JSON and pins exactly `@playwright/mcp@0.0.78` with the
  required flags, the identical pinned string appears in
  `.opencode/opencode.jsonc` (substring check — jsonc has comments, so
  no `json.loads` there), and the skill file exists with its
  frontmatter. These run inside the existing pytest step of
  `make verify` — same steps, no browser/network/MCP prerequisite —
  and earn their keep because two-config version drift is the most
  likely silent failure. ADR: n/a.
- **No CHANGELOG entry**: harness/contributor tooling, not a change
  package users see; docs live in `docs/harness-usage.md` + ADR 0009.
  ADR: n/a.

## Phase 1 — Harness wiring: config, ADR 0009, skill, docs, guards

**Scope.** Everything verifiable without a live MCP server: both
harness configs (version-pinned), ADR 0009, the `ui-parity-check`
skill encoding the full 14-item workflow, the docs update, the
gitignore line, and the deterministic guard tests. `make verify`
behavior stays byte-identical in steps and prerequisites. No frontend
or package code is touched.

**Steps.**
1. Author `docs/adr/0009-playwright-mcp-browser-automation.md`:
   Playwright MCP selected (decisive capability: `--caps=vision`
   coordinate mouse tools for `<canvas>`); rejected alternatives from
   the spec's verified research (chrome-devtools-mcp, Puppeteer MCP,
   Selenium MCP, cloud services); pinned to 0.0.78 with manual-bump
   update policy; `--headless --isolated`; `browser_run_code_unsafe`
   never used; one-time browser install (`npx playwright install
   chromium` or system Chrome) kept out of `make verify`; note that
   first `npx` use fetches the package itself (network once), fully
   local/offline thereafter; harness tooling only — no Python/runtime
   dependency added.
2. Add `.mcp.json` at the repo root:
   `{"mcpServers": {"playwright": {"command": "npx", "args":
   ["@playwright/mcp@0.0.78", "--headless", "--isolated",
   "--caps=vision", "--browser", "chromium"]}}}`.
3. Add the `"mcp"` key to `.opencode/opencode.jsonc`: `"playwright":
   {"type": "local", "command": ["npx", "@playwright/mcp@0.0.78",
   "--headless", "--isolated", "--caps=vision", "--browser",
   "chromium"], "enabled": true}`,
   with a comment noting the version is kept in lockstep with
   `.mcp.json` and pinned by `tests/test_harness_config.py`.
4. Write `.agents/skills/ui-parity-check/SKILL.md` (house format per
   `.agents/skills/verify/SKILL.md`):
   - Frontmatter: `name: ui-parity-check`; trigger description ("run
     the UI parity check", "parity checklist", "frontend regression
     check", after any frontend change).
   - Prerequisites: session must have the approved `playwright` MCP
     server loaded (how to check: list its tools; if absent, tell the
     user to restart/approve — do not work around it); one-time
     browser install command.
   - Setup: the verbatim build/serve commands from the uplot
     checklist preamble (`uv run ulv build … --generator html-uplot`
     for the ASV fixture and the BMF fixture; `python3 -m http.server`
     from the parent dir so both sites are served from a
     subdirectory), and the both-sites-unless-named rule.
   - Per-item procedures — one entry per checklist item, naming the
     MCP tools and the pass criterion:
     1. *Nav tree + param selectors + sub-selection*:
        `browser_navigate`, `browser_click` (a11y refs — nav/selectors
        are DOM, not canvas), `browser_evaluate` for rendered series
        count; screenshot.
     2. *Log toggle / date–even x toggle*: `browser_click`,
        `browser_console_messages` (no errors), before/after
        screenshots.
     3. *Hover crosshair + tooltip*: `browser_evaluate`
        `getBoundingClientRect` on the chart canvas → compute a data
        point's viewport coords → `browser_mouse_move_xy`; read
        tooltip DOM via `browser_evaluate` (8-char hash, date, value,
        units text); screenshot. BMF units slug agent-verified; the
        live-Bencher human-readable units string is **confirm
        manually** (no live project in fixtures — stated reason).
     4. *Commit click-through*: `browser_mouse_click_xy` on a data
        point; verify the opened URL (new tab) matches
        `show_commit_url` + full hash; verify no commit page opens
        after finishing a drag-zoom nor ever from the overview strip.
     5. *Drag-zoom + overview + reset*: `browser_mouse_drag_xy` on
        main chart and overview strip; `browser_mouse_click_xy` with
        `clickCount: 2` to reset; `browser_evaluate` `location.hash`
        for `zoom=` appearing/disappearing; screenshots.
     6. *Legend toggle*: `browser_click` on legend entry; `hide=` in
        hash; screenshot.
     7. *Toggle-then-axis-change reset*: legend toggle →
        selector change via `browser_click` → `browser_evaluate` that
        no series is unexpectedly hidden.
     8. *Pinch-zoom/pan*: `browser_evaluate` dispatching synthetic
        `TouchEvent`s (two-finger pinch around midpoint, one-finger
        pan); final range lands in the hash on gesture end. Verdict
        cap: app-listener behavior can be agent-verified; native
        gesture *feel* on a real device is **confirm manually**
        (stated reason: synthetic events bypass browser gesture
        recognition).
     9. *2→1 finger transition*: same synthetic-TouchEvent technique;
        no jump in the evaluated x-range mid-gesture; feel residual as
        in item 8.
     10. *Grid lazy thumbnails + list sorting + no dead columns*:
         `browser_navigate` per view; scroll via `browser_press_key` /
         `browser_evaluate`; `browser_click` on sort headers;
         `browser_evaluate` column headers are exactly
         Benchmark / Last value / Error and sort order is correct;
         screenshots.
     11. *Hash round-trip*: compose state (benchmark + params + log +
         even x + zoom + one hidden series), read `location.hash`,
         `browser_navigate` to that URL fresh, `browser_evaluate`
         state equality; screenshots of both.
     12. *Phone-width viewport*: `browser_resize` to 375 px;
         `browser_evaluate` no horizontal overflow of page chrome
         (`scrollWidth <= innerWidth` on the scrolling element);
         screenshot.
     13. *Machine axis presence*: `browser_evaluate` selector groups —
         BMF site has no machine selector; ASV site shows machine as
         an ordinary axis group.
     14. *Network isolation*: `browser_network_requests` after
         browsing all three views; every request URL is under the
         site's own subdirectory, no external hosts; the full listing
         goes into the report verbatim.
   - Report contract: path
     `specs/<target-feature>/parity-report-<YYYY-MM-DD>.md` (target
     spec dir is the invocation parameter; default for the first run:
     `specs/2026-07-uplot-frontend/`); 14 items in checklist order;
     three-way verdict vocabulary verbatim; inline textual evidence
     per item; screenshots saved to
     `specs/<target-feature>/parity-evidence/` (gitignored) and
     referenced by filename; anything flaky or unverifiable is
     "confirm manually" with a reason — never silently passed.
   - Gotchas: leave an explicit `TODO(first run)` placeholder for the
     empirically confirmed coordinate semantics of the `*_xy` tools
     (expected: viewport-level CSS px), to be filled by Phase 2.
5. Confirm the skill symlink layout: expected directory-level
   symlinks (`.claude/skills` → `.agents/skills`, `.opencode/skills` →
   `.agents/skills`) so the new skill dir appears in both harnesses
   with no extra wiring; if the layout is per-skill, add the two
   matching symlinks. Update the skills `README.md` if it enumerates
   skills.
6. Add `specs/*/parity-evidence/` to the root `.gitignore` (in the
   agent-scratch block, alongside `specs/*/scratch.md`).
7. Update `docs/harness-usage.md`: a short "Browser automation (MCP)"
   section — what the `playwright` server is for, the one-time
   approval flow in each harness (Claude Code prompts on first use of
   `.mcp.json`; OpenCode reads `opencode.jsonc`), the one-time browser
   install, how to invoke the `ui-parity-check` skill, and a link to
   ADR 0009.
8. Add `tests/test_harness_config.py` (stdlib only): `.mcp.json` is
   valid JSON, its `playwright` entry's args contain exactly
   `@playwright/mcp@0.0.78` plus `--headless`, `--isolated`,
   `--caps=vision`, `--browser chromium`, and no `@latest`; the identical
   `@playwright/mcp@0.0.78` string appears in
   `.opencode/opencode.jsonc`; `.agents/skills/ui-parity-check/SKILL.md`
   exists and starts with frontmatter containing `name:` and
   `description:`.
9. Run `make verify`; confirm the step list and prerequisites are
   identical to before the change (spec criterion), and diff the
   package dependency declarations (`pyproject.toml`) to confirm no
   new Python/runtime dependency.

**Tests.** New `tests/test_harness_config.py` (runs inside the
existing pytest step); all existing suites unchanged and green.
**Exit criteria.** ADR 0009, both configs, skill, docs, gitignore
line, and guards merged; `make verify` green with identical steps and
no new prerequisites; no dependency-declaration diff. (Fresh-session
tool listing is deliberately *not* an exit criterion here — it cannot
be observed from the session that creates the config; it opens
Phase 2.)

## Phase 2 — First recorded run (fresh session, server approved)

**Scope.** Executed standalone in a *new* session started after
Phase 1 is merged and the user has approved the `playwright` MCP
server. Confirms the server loads in both harnesses, empirically
confirms coordinate semantics and tool behavior (recorded into the
skill), runs the full 14-item check against both fixture sites, and
produces the committed evidence report for the uplot feature's
sign-off review. No code changes beyond the skill-gotchas edit and
checklist annotation.

**Steps.**
1. Preconditions (self-contained; do not assume memory of Phase 1):
   fresh Claude Code session in the repo root; approve the
   `playwright` MCP server when prompted; confirm its tools are
   listed. Separately, start a fresh OpenCode session and confirm the
   same tool listing (this discharges the both-harnesses spec
   criterion; record both observations in the report's preamble). If
   the browser binary is missing, run `npx playwright install
   chromium` once.
2. Empirical calibration (first task of the run, per the skill's
   `TODO(first run)`): serve a fixture site, `browser_evaluate`
   `getBoundingClientRect` on a known element, `browser_mouse_click_xy`
   at those coordinates, and confirm the `*_xy` tools take
   viewport-level CSS px; likewise sanity-check `browser_mouse_drag_xy`
   select behavior and double-click via `clickCount: 2` on the chart.
   Replace the skill's placeholder gotcha with the confirmed semantics
   (promoting the durable finding, per house convention).
3. Invoke the `ui-parity-check` skill targeting
   `specs/2026-07-uplot-frontend/`: build both fixture sites, serve
   from the subdirectory, and drive all 14 items on both sites per the
   skill's procedures, capturing screenshots to
   `specs/2026-07-uplot-frontend/parity-evidence/`.
4. Write `specs/2026-07-uplot-frontend/parity-report-<date>.md` per
   the report contract: 14 verdicts in the three-way vocabulary;
   inline textual evidence; the network-isolation item includes the
   verbatim recorded request listing; the two residual items (touch
   feel, live-Bencher units) marked "confirm manually" with stated
   reasons; any item the agent could not reliably verify likewise —
   never silently passed.
5. Annotate each of the 14 checklist items in
   `specs/2026-07-uplot-frontend/tasks.md` with its verdict and a
   reference to the report. **Do not tick the boxes** — the checklist
   is "HUMAN PASS REQUIRED"; ticking is the owner's act at sign-off,
   now reduced to reviewing the report plus the flagged items.
6. If any item comes back **agent-verified fail**: record it in the
   report as-is; fixing the frontend is explicitly separate work (spec
   non-goal) — flag it to the owner, do not patch frontend code in
   this feature.
7. Run `make verify` (still green, still unchanged).

**Tests.** No new automated tests (by design — spec Decision 3); the
committed report is the verification artifact; Phase 1's guard tests
and all existing suites stay green.
**Exit criteria.** Tool listing confirmed and recorded for both
harnesses from fresh sessions; the skill ran end to end without
manual intervention; `parity-report-<date>.md` exists with exactly 14
verdicts matching the checklist one-to-one, the 2 permanent residuals
"confirm manually" with reasons (target: the other 12 agent-verified);
screenshots present locally under `parity-evidence/`; skill gotcha
updated with confirmed coordinate semantics; uplot `tasks.md`
annotated; owner has everything needed for the shortened sign-off
review.

## Risks & open questions

- **Coordinate semantics assumption wrong** (device px, or offset by
  browser chrome): calibration is the mandatory first task of Phase 2,
  before any verdict is recorded; the confirmed semantics are written
  into the skill so future runs never re-derive them.
- **Fresh-session bootstrapping fails** (server not offered for
  approval, or tools missing): the config is inert data — debug by
  comparing against the pinned shapes in this plan and the guard test;
  nothing in `make verify` depends on it, so the repo stays green
  while iterating.
- **Canvas interactions flaky** (tooltip timing, drag thresholds,
  new-tab capture on commit click-through): the verdict vocabulary
  absorbs this — a flaky item becomes "confirm manually" with a
  reason, never a silent pass (spec Decision 6); the report stays
  honest even on a bad run.
- **`npx` cold start needs the network once** to fetch
  `@playwright/mcp@0.0.78` (then cached): documented in ADR 0009 and
  `docs/harness-usage.md` as part of the one-time setup, alongside the
  browser install; never triggered by `make verify`.
- **Skill drift vs. the checklist**: the skill hardcodes the 14 items
  of a completed feature. Accepted: the checklist is the regression
  contract for future frontend changes too; if a future feature
  changes the parity surface, its plan updates the skill — the fixed
  14-item report format makes any mismatch visible at review.
- **jsonc guard brittleness**: `opencode.jsonc` can't be
  `json.loads`-ed; the guard is a substring check on the pinned
  version string only — deliberately minimal so formatting/comment
  churn can't break it.
