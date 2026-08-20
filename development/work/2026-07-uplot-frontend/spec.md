# Modern Lightweight HTML Frontend (uPlot) as an Alternative Output Generator

## Problem

ulv's only HTML output generator ships the vendored ASV frontend: jQuery
3.3.1 + flot 0.8.3 + Bootstrap 3.1.1 + glyphicon fonts, ~604 KB on disk.
Every library in that stack is dead or EOL upstream (flot's last release
is from ~2014), so there is no upgrade path — only a growing set of local
patches: `VENDORED.md` records eight, three of them behavioral fixes for
machine-less BMF/Bencher datasets that violate ASV's hard-coded `machine`
axis assumptions. The coupling costs show up everywhere: end-to-end tests
re-implement vendored JS logic in Python and assert on literal JS
strings; the frontend recomputes graph file paths client-side, forcing
the Python side to mirror ASV's path sanitization byte-for-byte (and to
vendor an md5 library), which already produced one shipped bug class
(Bencher-style benchmark names 404ing their thumbnails). The site is not
mobile-responsive, and viewers on weak or mobile devices pay the full
~604 KB payload. Every future dataset shape that ASV never anticipated
means another hand-maintained patch against abandoned code.

## Goal

ulv offers a second, selectable HTML output generator — a self-authored,
framework-free frontend built on a single small vendored chart library —
that reaches feature parity with the current generator's browsing
experience in under ~100 KB, treats machine-less datasets as
first-class, and is mobile-responsive, while the existing vendored
generator continues to work unchanged as the default.

## Users & stakeholders

- **Project maintainers** who publish dashboards and want a smaller,
  faster, mobile-friendly site they can keep maintaining without
  patching abandoned third-party code.
- **Contributors and performance engineers** who browse generated sites,
  increasingly from phones and low-powered machines.
- **Bencher/BMF users**, whose machine-less datasets currently work only
  through behavioral patches to the vendored frontend.
- **ulv's own developers/agents**, who inherit the maintenance burden of
  the vendored patches and the fragile JS-string-asserting tests; the
  new frontend is code they own end to end.
- **Existing users of the vendored generator**, who must be unaffected:
  their default output does not change.
- **Sign-off:** the project owner (repository owner).

## Background research

Two adversarial deep-research passes (2026-07-18, verified against
primary sources) compared candidate chart libraries against the
project's constraints: lightweight and fast on weak and mobile devices,
maintainable by this project, desktop + mobile support, and durably
FOSS. Verdict: uPlot (MIT, zero-dependency, canvas-based, ~50 KB
minified / ~22 KB gzipped) beats every specialized alternative examined
(Chart.js, ECharts, Plotly, ApexCharts, dygraphs, Chartist, Frappe,
lightweight-charts) and every general-purpose one (D3, Observable Plot,
Vega/Vega-Lite, billboard.js, BokehJS, Perspective, PixiJS/WebGL) on
those constraints. ECharts is the documented fallback if uPlot becomes
untenable. Known uPlot gaps and mitigations: touch pinch-zoom is
provided via its official plugin/hooks approach rather than core; the
single-maintainer bus-factor risk is mitigated by vendoring a pinned
file against a tiny, stable API.

## Success criteria

- The new generator is selectable through the existing output-generator
  plugin mechanism, and selecting it produces a complete static site
  from the same datasets the current generator accepts — verified by
  building sites from the existing ASV, BMF, and Bencher test fixtures
  with the new generator and browsing them without errors.
- The vendored generator remains the default and its output is
  unchanged — verified by the existing generator's test suite passing
  unmodified and by confirming a build with no generator selection still
  uses it.
- Total shipped frontend payload for the new generator (HTML + CSS + JS
  + vendored chart library + plugins, everything the site serves besides
  data files) is under 100 KB on disk — verified by an automated test
  that sums the byte sizes of the new generator's static assets.
- Feature parity with the current frontend's actual behavior, each item
  verified by exercising it in a built site: benchmark tree navigation;
  per-axis parameter selectors and benchmark-parameter sub-selection;
  log-scale toggle; date vs. even-spacing x-axis toggle; overview
  mini-plot with drag-select zoom; hover crosshair/tooltip; click-through
  from a data point to its commit URL (honoring the configured commit
  URL template and hash length); series legend with per-series toggling;
  lazy-loaded grid view of thumbnails; sortable list view; a snapshot
  page for datasets without a time axis.
- The list view does not include the "Recent change"/"Changed at"
  columns (ulv always emits null for them) — verified by inspecting the
  rendered list view for a fixture site.
- View state (selected benchmark, parameter selections, toggles, zoom)
  round-trips through the URL hash: copying the URL from one browsing
  session and opening it fresh restores the same view — verified for a
  representative selection of states.
- A machine-less dataset (BMF/Bencher fixture) renders its graphs with
  no machine selector shown and no errors, and a dataset with machines
  shows machine as an ordinary parameter axis — verified on one fixture
  of each kind.
- When a benchmark carries a human-readable units string (Bencher
  measure units), the new frontend displays it with the plotted values —
  verified on a Bencher fixture with units, closing the gap recorded in
  the architecture notes.
- The frontend obtains every graph data file's path from an explicit
  manifest emitted in the site's index data rather than recomputing
  sanitized paths client-side — verified by building a site whose
  benchmark names sanitize differently from their raw form (e.g.
  Bencher-style names) and confirming every graph and thumbnail loads.
- The index-data manifest addition is purely additive: the existing
  vendored frontend consumes the extended index data unchanged —
  verified by the vendored generator's tests passing against the
  extended format.
- Touch devices can pinch-zoom and pan graphs — verified by simulated
  touch gesture events in a browser test (or a documented manual check
  if simulation proves unreliable).
- The layout is usable on a narrow (phone-width) viewport: navigation,
  selectors, and graphs are reachable without horizontal scrolling of
  the page chrome — verified by rendering at a mobile viewport width and
  checking layout assertions.
- The generated site works when hosted under a non-root URL path —
  verified by serving it from a subdirectory and crawling/browsing it
  with no broken assets or links.
- The generated site performs no network requests other than fetching
  its own static files, and contains no absolute URLs to external
  hosts — verified by inspecting requests while browsing and scanning
  the emitted files.
- All vendored third-party files for the new frontend are pinned with
  recorded versions, sources, and integrity hashes, with licenses
  attributed — verified by inspecting the vendoring record and license
  files, matching the rigor of the existing `VENDORED.md`.
- The built wheel/sdist includes the new generator's complete static
  asset tree — verified by building the package and generating a site
  from the installed artifact.
- The decision to add the chart library and supersede the "reuse ASV
  UI" choice is recorded as a new ADR that carries forward the existing
  vendoring policy — verified by the ADR's presence and content.
  (Authoring it happens in the plan/build phases; this spec only
  requires that it exist before the feature is called done.)

## Non-goals

- **Flipping the default generator.** The vendored generator stays the
  default; changing that is a separate, later decision after parity is
  demonstrated in real use.
- **Removing or deprecating the vendored generator.** The two coexist;
  no code or docs removal for the old one.
- **Regression/step detection.** Unchanged from the prior spec
  (Decision 6): no change columns, no detection, no alerting.
- **A JS build toolchain.** No bundler, transpiler, package manager, or
  build step for the frontend; plain files only.
- **Legacy browser support.** No Internet Explorer or otherwise
  end-of-life browsers; modern evergreen desktop and mobile browsers
  only.
- **Changing the Python data layer's computations.** Graph resampling,
  gap-fill, and geometric-mean summaries, and the graph data file
  content format, stay as-is; the only data contract change is the
  additive index manifest.
- **New visualization features beyond parity** (e.g. series comparison
  overlays, annotations, dashboards). Parity first; extras are future
  work.

## Decisions

1. **Chart library: uPlot, vendored under the existing vendoring
   policy** (pinned plain files, recorded sources and integrity hashes,
   a vendoring record, license attribution). A new ADR will supersede
   the current ADR's "reuse ASV UI" choice while carrying its vendoring
   policy forward. Rationale: the adversarially verified research
   verdict above; ECharts is the documented fallback.
2. **App shell: self-authored vanilla JS and modern CSS (flex/grid).**
   No framework, no Bootstrap, no jQuery, no JS build toolchain.
   Mobile-responsive layout is in scope — the current frontend has
   none. Rationale: the app shell is small enough to own outright, and
   every framework adds payload, churn, and a second dependency
   treadmill.
3. **The Python data layer stays as-is, with one additive contract
   change:** the site's index data gains an explicit
   graph-key → file-path manifest so the frontend never recomputes
   sanitized paths client-side. This eliminates the byte-for-byte
   path-mirroring requirement and the md5 vendoring, and closes the bug
   class behind patch 6. Additive only — the existing vendored frontend
   must keep working against the extended format.
4. **`machine` is just an optional parameter axis** in the new
   frontend. Machine-less datasets (BMF/Bencher) are first-class, not a
   patched-in special case — eliminating the bug class behind patches 7
   and 8.
5. **Feature parity targets are the current frontend's actual
   behavior** (enumerated in the success criteria), with one deliberate
   subtraction: the permanently empty "Recent change"/"Changed at" list
   columns are dropped rather than shipped as dead UI.
6. **Touch pinch-zoom/pan via the chart library's official
   plugin/hooks approach**, vendored and owned by this project, since
   it is not core library functionality.
7. **Coexistence via the existing output-generator plugin mechanism.**
   The new generator is selectable; the vendored generator remains the
   default until parity is demonstrated. Flipping the default is a
   separate later decision, out of scope here.
8. **Payload budget: under ~100 KB total shipped frontend** — at least
   6x smaller than the current ~604 KB — enforced as an automated
   acceptance test, not a guideline.
9. **Regression/step detection remains out of scope**, unchanged from
   the prior spec's Decision 6.
10. **Same hosting constraints as the prior spec:** no external network
    requests, and the site must work served from a subdirectory (e.g. a
    GitHub Pages project page).

## Open questions

- None blocking. One flag for the Architect: the exact shape of the
  index-data manifest (Decision 3) is an implementation choice, but the
  compatibility requirement — the vendored frontend must consume the
  extended index unchanged — is binding.
