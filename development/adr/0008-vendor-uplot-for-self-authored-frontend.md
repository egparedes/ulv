# 8. Vendor uPlot for a self-authored second HTML frontend

## Status

Accepted

Supersedes the "reuse ASV's web UI" frontend choice of ADR 0003 for
the new `html-uplot` generator. ADR 0003 itself remains in force: it
governs the vendored ASV frontend, which continues to ship unchanged
as the default `html` generator.

## Context

ADR 0003 vendored ASV's browsing UI: jQuery 3.3.1 + flot 0.8.3 +
Bootstrap 3.1.1 + glyphicon fonts, ~604 KB on disk. Every library in
that stack is dead or EOL upstream, so there is no upgrade path — only
a growing set of local patches (eight recorded in
`src/ulv/outputs/html/VENDORED.md`, three of them behavioral fixes for
machine-less datasets). The coupling forces the Python side to mirror
ASV's path sanitization byte-for-byte and the tests to re-implement
vendored JS logic; the site is not mobile-responsive.

The uplot-frontend spec adds a second, selectable generator with a
self-authored frontend built on one small vendored chart library.
Two adversarial research passes (2026-07-18) compared candidates
against the constraints — lightweight on weak/mobile devices,
maintainable here, desktop + mobile, durably FOSS — and uPlot (MIT,
zero-dependency, canvas-based, ~50 KB minified) beat every specialized
and general-purpose alternative examined. ECharts is the documented
fallback if uPlot becomes untenable.

## Decision

- Vendor **uPlot, pinned to an exact release** (1.6.32 at vendoring
  time), as two plain files — `uPlot.iife.min.js`, `uPlot.min.css` —
  under `src/ulv/outputs/html_uplot/static/vendor/`.
- Carry ADR 0003's vendoring policy forward: pinned files, recorded
  source URLs and sha256 integrity hashes in
  `src/ulv/outputs/html_uplot/VENDORED.md`, license text under
  `src/ulv/outputs/html_uplot/LICENSES/`. Because npm tarballs carry
  no SRI annotations, integrity comes from fetching each file from two
  independent sources (npm registry tarball and jsDelivr) and
  verifying the hashes agree; both provenance URLs are recorded and
  the hashes are pinned in an automated test.
- **No local patches to the vendored files.** Behavior gaps (e.g.
  touch pinch-zoom, which uPlot leaves to its plugin/hooks approach)
  are closed in our own app-shell code, which is plain ES modules and
  CSS with no framework or build toolchain.
- The app shell plus vendored library are held **under a 100,000-byte
  payload budget**, enforced by a test rather than a guideline.
- Update policy: manual re-vendor of a newer pinned release, hashes
  re-verified from two sources; fallback if uPlot dies upstream is a
  re-vendor onto ECharts under this same policy.

## Consequences

- The new frontend is code this project owns end to end: no more
  patch stack against abandoned code, and machine-less datasets need
  no special-casing.
- The `graph_paths` manifest in `index.json` replaces client-side path
  recomputation, so the new frontend needs no md5 vendoring and is
  immune to the sanitized-path bug class.
- Two frontends must be maintained while both ship; the default stays
  the vendored generator until parity is demonstrated (flipping it is
  a separate, later decision).
- uPlot's single-maintainer bus factor is accepted: the API surface
  used is tiny, the file is pinned, and the ECharts fallback is
  recorded here.
- The payload-budget test makes any future third-party addition to the
  new frontend a deliberate decision (it would have to fit the budget
  and revisit this ADR).
