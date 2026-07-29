# Tasks

Mirror of `plan.md`. Tick as you go; every phase ends with
`make verify` green. Phase 2 MUST run in a fresh session started after
Phase 1 is merged and the `playwright` MCP server is user-approved.

## Phase 1 — Harness wiring: config, ADR 0009, skill, docs, guards

- [x] Author `docs/adr/0009-playwright-mcp-browser-automation.md`:
      choice + rejected alternatives, pin 0.0.78 + manual-bump policy,
      `--headless --isolated --caps=vision`, no
      `browser_run_code_unsafe`, one-time browser install kept out of
      `make verify`, npx-cold-start network note, no runtime dep
- [x] `.mcp.json` at repo root: `playwright` server via
      `npx @playwright/mcp@0.0.78 --headless --isolated --caps=vision`
- [x] `"mcp"` key in `.opencode/opencode.jsonc`: same pinned command,
      `"type": "local"`, `"enabled": true`; lockstep comment
- [x] `.agents/skills/ui-parity-check/SKILL.md`: frontmatter +
      trigger description; prerequisites (approved server, browser
      install); verbatim build/serve setup from the uplot checklist
      preamble; per-item procedures for all 14 items (tools + pass
      criteria; residual items capped at "confirm manually" with
      reasons); report contract (path, 14 items in order, three-way
      verdicts, inline textual evidence, gitignored screenshots);
      `TODO(first run)` gotcha placeholder for coordinate semantics
- [x] Confirm skill symlink layout exposes the new skill in both
      harnesses (directory-level expected); add per-skill symlinks
      only if needed; update skills README if it enumerates skills
      (confirmed directory-level: `.claude/skills` and
      `.opencode/skills` both symlink `.agents/skills`; README does
      not enumerate — no changes needed)
- [x] `.gitignore`: add `specs/*/parity-evidence/`
- [x] `docs/harness-usage.md`: "Browser automation (MCP)" section —
      approval flow per harness, one-time browser install, invoking
      `ui-parity-check`, link to ADR 0009
- [x] `tests/test_harness_config.py` (stdlib only): `.mcp.json` valid
      JSON + exact pin + flags + no `@latest`; same pin string in
      `.opencode/opencode.jsonc`; skill file exists with frontmatter
- [x] `make verify` green with identical steps/prerequisites; no
      `pyproject.toml` dependency diff

## Phase 2 — First recorded run (fresh session, server approved)

- [ ] Fresh Claude Code session: approve `playwright` server, confirm
      tools listed; fresh OpenCode session: confirm same; record both
      in the report preamble; `npx playwright install chromium` once
      if the browser is missing
- [ ] Calibration: confirm `*_xy` tools take viewport CSS px (via
      `getBoundingClientRect` + `browser_mouse_click_xy`), sanity-check
      drag-select and `clickCount: 2`; replace the skill's
      `TODO(first run)` gotcha with the confirmed semantics
- [ ] Invoke `ui-parity-check` targeting
      `specs/2026-07-uplot-frontend/`: build ASV + BMF sites, serve
      from subdirectory, drive all 14 items on both sites,
      screenshots to `parity-evidence/`
- [ ] Write `specs/2026-07-uplot-frontend/parity-report-<date>.md`:
      14 verdicts (three-way vocabulary), inline textual evidence,
      verbatim request listing for network isolation, residual items
      "confirm manually" with reasons, nothing silently passed
- [ ] Annotate the 14 checklist items in
      `specs/2026-07-uplot-frontend/tasks.md` with verdict + report
      reference; do NOT tick the boxes (owner's act at sign-off)
- [ ] Any agent-verified fail: recorded in the report and flagged to
      the owner; no frontend patching in this feature
- [ ] `make verify` green
