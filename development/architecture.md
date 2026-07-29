# Architecture

## High-level

Unladen Velocity (`ulv`) turns existing benchmark result data — native
ASV results, Bencher Metric Format files, or results fetched from a
Bencher server — into a self-contained static HTML site servable by any
plain file server:

```
input plugin ──> Dataset (ulv.model) ──> output generator ──> static site
   (asv, bmf,                              (html: vendored ASV frontend,
    bencher-api)                            html-uplot: uPlot frontend)
```

Two output generators share one data pipeline (`ulv.outputs.common`):
the default `html` (vendored ASV frontend) and the selectable
`html-uplot` (self-authored uPlot frontend, [ADR 0008](adr/0008-vendor-uplot-for-self-authored-frontend.md)),
chosen with `--generator` / the `output_generator` config key.

Typical invocations:

```
ulv build -i asv --input-dir results/ -o site/ --project myproj
ulv build -i asv --input-dir results/ -o site/ --repo . --branches main,dev
ulv build -i bmf --input-dir bmf/ --manifest bmf/manifest.json -o site/
ulv build -i bmf --input-dir bmf/ --filename-pattern "{commit}_{date}.json" -o site/
ulv build -i bencher-api --bencher-project myproj -o site/
ulv build --config ulv.toml
ulv serve site/ --port 8080
```

## Module map

| Module | Owns |
| --- | --- |
| `ulv.model` | Frozen `Dataset` (`Revision`, `Environment`, `Benchmark`, `ResultSeries`, `ResultPoint`); referential-integrity validation; `has_time_axis` (a single-revision dataset renders as a snapshot table, not graphs) |
| `ulv.plugins` | `InputFormat`/`OutputGenerator` protocols, per-kind registries, entry-point discovery ([ADR 0002](adr/0002-plugin-discovery-via-entry-points.md)) |
| `ulv.errors` | `UlvError(message, offending_input=…)`, the single user-facing error type; the CLI maps it (and `OSError`) to a one-line diagnostic + exit 1 |
| `ulv.config` | `Settings` dataclass, TOML/JSON config loading, precedence defaults < file < flags ([ADR 0004](adr/0004-argparse-cli-with-config-file-precedence.md)) |
| `ulv.testbeds` | User-supplied testbed → factor decomposition (spec Decisions 8-9); shared by every input with a testbed notion |
| `ulv.gitrepo` | Read-only `git` CLI wrapper for optional enrichment (topological order, committer dates, tags, first-parent branch membership) |
| `ulv.cli` | argparse CLI: `build`, `serve` |
| `ulv.inputs.asv` | Native ASV results directories (api_version 2), lossless mapping, optional git enrichment |
| `ulv.inputs.bmf` | Bencher Metric Format files with explicit sidecar metadata (manifest / filename pattern / flags) |
| `ulv.inputs.bencher_api` | Read-only paginated fetch from a Bencher server ([ADR 0005](adr/0005-stdlib-http-client-with-transport-seam.md)) |
| `ulv.outputs.common` | Shared site-build pipeline for both generators: atomic output swap, graph building, summarylist rows, `index.json`/`info.json` data (including the `graph_paths` manifest), snapshot table extraction |
| `ulv.outputs.html.generator` | Default `html` generator: vendored static tree + snapshot page over the shared pipeline |
| `ulv.outputs.html.graphs` | Port of asv's graph data handling (averaging, NA trim, summary geometric means, resampling) minus step detection |
| `ulv.outputs.html.paths` | Graph file paths, byte-compatible with the vendored frontend's `graph_to_path`; also the source of the `graph_paths` manifest |
| `ulv.outputs.html.static/` | Vendored ASV frontend + pinned third-party libraries ([ADR 0003](adr/0003-vendor-asv-frontend-and-third-party-js.md)); patches and hashes in [`VENDORED.md`](../src/ulv/outputs/html/VENDORED.md), attributions in `LICENSES/` |
| `ulv.outputs.html_uplot.generator` | Selectable `html-uplot` generator: self-authored static tree + snapshot page over the shared pipeline ([ADR 0008](adr/0008-vendor-uplot-for-self-authored-frontend.md)) |
| `ulv.outputs.html_uplot.static/` | Self-authored app shell (plain ES modules + CSS, <100 KB budget, no `machine` special-casing) + pinned uPlot under `vendor/`; hashes in [`VENDORED.md`](../src/ulv/outputs/html_uplot/VENDORED.md), attribution in `LICENSES/` |

## Plugin architecture

Two registries in `ulv.plugins` (`input_formats`, `output_generators`)
hold the built-ins, registered at import time. Adding a format or
generator without touching shipped code:

- **Installed package:** expose an entry point in group
  `ulv.input_formats` or `ulv.output_generators` pointing at a class
  (instantiated with no arguments) or a ready instance.
- **In-process:** call `input_formats.register(plugin)` /
  `output_generators.register(plugin)`.

An input format provides `name` and `load(source, options) -> Dataset`;
an output generator `name` and `generate(dataset, out_dir, options)`.
Explicit registrations always win over entry points, so a third-party
package can never shadow a built-in ([ADR 0002](adr/0002-plugin-discovery-via-entry-points.md)).

## Semantics worth knowing

- **Revision numbering is dense.** Revisions are numbered by their
  index in the dataset (0..n-1), unlike asv, which numbers by position
  in the full `rev-list --all` history. Consequence: tags pointing at
  commits with no benchmark results are dropped rather than given a
  revision number.
- **Commit dates use the committer date (`%ct`).** asv reads the
  author date (`%at`); the two differ only for rebased or
  cherry-picked commits.
- **Branch attribution is per containing branch.** With a repository
  configured, a result is graphed once on every configured branch
  containing its commit (asv's semantics); results on no configured
  branch, or whose commit history no longer contains, are warned about
  and skipped, never mis-attributed.
- **BMF ordering is metadata-only** (spec Decision 3): a manifest,
  a filename pattern, or per-file flags — never file order, name
  order, or mtimes. A lone snapshot needs no metadata and renders as a
  table (`snapshot.html`, with `index.html` a redirect to it).
- **Output is atomic.** Sites build in a hidden sibling directory and
  swap in on success; a failed build leaves either no output or the
  previous site intact.

## The `graph_paths` manifest

`index.json` carries one additive top-level key, `graph_paths`, so a
frontend never recomputes sanitized file paths client-side (the bug
class behind vendored patch 6):

```json
"graph_paths": {
  "dirs": ["graphs/branch-main/machine-cheetah/…", "…"],
  "summary_dir": "graphs/summary",
  "benchmarks": {"adapter::json (latency)": "adapter__json (latency)"}
}
```

- `dirs` is **parallel to `graph_param_list`** (entry *i*'s files live
  in `dirs[i]`). It is a separate array — never a key inside the
  entries — because the vendored `graph_to_path` iterates entry keys.
- `benchmarks` maps every raw benchmark name to its sanitized file
  stem (no `.json`).
- Any graph URL is `dir + "/" + stem + ".json"`; each environment
  directory also holds its summarylist rows at `dir + "/summary.json"`,
  and grid thumbnails live at `summary_dir + "/" + stem + ".json"`.
  Clients apply `encodeURIComponent` per path segment.
- Both sides derive from the same `ulv.outputs.html.paths` functions,
  so the manifest and the on-disk layout cannot drift. The addition is
  purely additive: the vendored frontend ignores unknown index keys.

The `html-uplot` frontend fetches exclusively through this manifest;
the vendored frontend still recomputes paths (unchanged by design).

## External dependencies

None at runtime. The stdlib covers TOML/JSON config (`tomllib`,
`json`), HTTP fetch (`urllib.request`, [ADR 0005](adr/0005-stdlib-http-client-with-transport-seam.md)),
the CLI (`argparse`, [ADR 0004](adr/0004-argparse-cli-with-config-file-precedence.md)),
and the preview server (`http.server`). Git enrichment shells out to
the `git` CLI. The vendored frontend third-party JS/CSS is pinned and
attributed per [ADR 0003](adr/0003-vendor-asv-frontend-and-third-party-js.md).

## Boundaries

- **CLI**: `ulv build` (read inputs, write a site), `ulv serve`
  (local preview only — the published site needs no server logic).
- **Outbound HTTP**: only the `bencher-api` input, read-only GETs.
- **Generated sites** perform no network requests beyond fetching
  their own static files.

## Deferred / future work

- **Git enrichment for BMF/Bencher inputs** (plan Phase 8 step 2
  anticipated it): the `bmf` and `bencher-api` inputs reject the
  `repo`/`branches` settings with explicit errors instead of wiring
  `ulv.gitrepo` in. Their ordering is metadata-/timestamp-driven by
  design (spec Decision 3); enriching commit order and links from a
  repository is compatible with the model (`Revision` already carries
  the fields) and can be added behind the existing settings without
  breaking anything.
- **Regression detection** is out of scope for v1 (spec Decision 6):
  summarylist change columns stay null; asv's `step_detect` was
  deliberately not ported.
- **Bencher measure units in the vendored frontend**: the
  human-readable units string rides in `Benchmark.extra["units"]` and
  the `html-uplot` frontend displays it (y-axis label, tooltip, list
  view); the vendored frontend still shows the measure slug — closing
  that would mean another patch against abandoned code.

## Generated code

Anything under `*/generated/` is regenerated by your project's codegen
pipeline (define it as a target in your task runner or as a standalone
script). Agents must not edit generated files. (`src/ulv/outputs/html/static/`
is vendored, not generated — see `VENDORED.md` — and is excluded from
lint/format instead.)

## See also

- ADRs of record: [`adr/`](adr/) — notably
  [0002 plugin discovery](adr/0002-plugin-discovery-via-entry-points.md),
  [0003 vendored frontend](adr/0003-vendor-asv-frontend-and-third-party-js.md),
  [0004 argparse + config precedence](adr/0004-argparse-cli-with-config-file-precedence.md),
  [0005 stdlib HTTP transport](adr/0005-stdlib-http-client-with-transport-seam.md),
  [0008 uPlot frontend](adr/0008-vendor-uplot-for-self-authored-frontend.md)
- Style guide: [`style.md`](style.md)
- Testing strategy: [`testing.md`](testing.md)
