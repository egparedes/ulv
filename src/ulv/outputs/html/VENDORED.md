# Vendored frontend assets

See ADR 0003 (`development/adr/0003-vendor-asv-frontend-and-third-party-js.md`).

## ASV web UI (`static/`, excluding `static/vendor/`)

Copied from `asv/www/` at upstream commit
`7032df701a969fa61f4c819ce9f71fb2e66f5a62` of
<https://github.com/airspeed-velocity/asv> (BSD-3-Clause).

Files **not** copied (regression detection is out of scope, spec
Decision 6): `regressions.js`, `regressions.css`.

Patches applied to `index.html` (everything else is verbatim):

1. The ten CDN `<script>`/`<link>` tags replaced with relative
   `vendor/…` tags; `integrity`/`crossorigin`/`referrerpolicy`
   attributes dropped (same-origin local files), `onerror`
   handlers kept.
2. Removed the `regressions.js` script tag and `regressions.css`
   link tag.
3. Removed the Regressions nav item (`<li id="nav-li-regressions">`).
4. Removed the `#regressions-display` div.
5. Removed the atom-feed link (`regressions.xml`).

Patch applied to `summarygrid.js` (everything else is verbatim):

6. The grid thumbnail fetch `'graphs/summary/' + bm.name + '.json'`
   (line 65 upstream) is replaced with
   `$.asv.graph_to_path(bm.name, {summary: ''})`. Summary files are
   written at the sanitized benchmark name, but the raw concatenation
   only resolves when the name sanitizes to itself — true for ASV's
   dotted identifiers, false for Bencher-style names like
   `adapter::json (latency)`, whose thumbnails 404'd. `graph_to_path`
   applies the same sanitize+URI-encode as every other graph fetch and
   already appends `.json`.

Patches for datasets without a `machine` axis (ASV data always has
one, so upstream never exercises these paths; BMF/Bencher data has
testbeds or user-declared factors instead):

7. `graphdisplay.js`: `state.machine = index.params.machine` (line 369
   upstream) and the machine selector panel (line 465) are guarded on
   `index.params.machine !== undefined`. Unguarded, the undefined
   `machine` state key made the graph permutation filter reject every
   `graph_param_list` candidate ("No graphs to load.") and rendered an
   empty machine panel. All other `state.machine`/`index.machines`
   uses sit inside the guarded panel callback.
8. `summarylist.js`: the same two guards (lines 126 and 151 upstream).
   Here the unguarded code was near-benign (jQuery's `$.each` no-ops
   on undefined and `get_valid_state` replaces the state wholesale)
   but still rendered an empty machine panel.

## Third-party libraries (`static/vendor/`)

Downloaded once from the URLs pinned in ASV's `index.html` at the
commit above and verified against the integrity hashes recorded there:

| File | Version | Source | Integrity |
| --- | --- | --- | --- |
| `jquery-3.3.1.min.js` | 3.3.1 | code.jquery.com | `sha256-FgpCb/KJQlLNfOu91ta32o/NMZxltwRo8QtmkMRdAu8=` |
| `jquery.flot.min.js` | 0.8.3 | cdnjs | `sha512-eO1AKNIv7KSFl5n81oHCKnYLMi8UV4wWD1TcLYKNTssoECDuiGhoRsQkdiZkl8VUjoms2SeJY7zTSw5noGSqbQ==` |
| `jquery.flot.time.min.js` | 0.8.3 | cdnjs | `sha512-lcRowrkiQvFli9HkuJ2Yr58iEwAtzhFNJ1Galsko4SJDhcZfUub8UxGlMQIsMvARiTqx2pm7g6COxJozihOixA==` |
| `jquery.flot.selection.min.js` | 0.8.3 | cdnjs | `sha512-3EUG0t3qfbLaGN3FXO86i+57nvxHOXvIb/xMSKRrCuX/HXdn1bkbqwAeLd6U1PDmuEB2cnKhfM+SGLAVQbyjWQ==` |
| `jquery.flot.categories.min.js` | 0.8.3 | cdnjs | `sha512-x4QGSZkQ57pNuICMFFevIhDer5NVB5eJCRmENlCdJukMs8xWFH8OHfzWQVSkl9VQ4+4upPPTkHSAewR6KNMjGA==` |
| `jquery.flot.orderBars.js` | 1.0.0 | jsdelivr (flot-orderbars) | `sha256-OXNbT0b5b/TgglckAfR8VaJ2ezZv0dHoIeRKjYMKEr8=` |
| `stupidtable.min.js` | 1.0.1 | cdnjs | `sha512-GM3Ds3dUrgkpKVXc+4RxKbQDoeTemdlzXxn5d/QCOJT6EFdEufu1UTVBpIFDLd6YjIhSThNe+zpo1mwqzNq4GQ==` |
| `md5.min.js` | 2.19.0 | cdnjs (blueimp-md5) | `sha512-8pbzenDolL1l5OPSsoURCx9TEdMFTaeFipASVrMYKhuYtly+k3tcsQYliOEKTmuB1t7yuzAiVo+yd7SJz+ijFQ==` |
| `bootstrap.min.js` | 3.1.1 | jsdelivr | `sha256-iY0FoX8s/FEg3c26R6iFw3jAtGbzDwcA5QJ1fiS0A6E=` |
| `css/bootstrap.min.css` | 3.1.1 | jsdelivr | `sha256-6VA0SGkrc43SYPvX98q/LhHwm2APqX5us6Vuulsafps=` |

`bootstrap.min.css` references its glyphicon fonts relatively
(`../fonts/…`), so those ship too, from the same bootstrap@3.1.1
jsdelivr distribution, and the CSS sits in `css/` to preserve the
upstream `dist/css` + `dist/fonts` layout that reference assumes.
ASV's `index.html` does not SRI-pin fonts; the hashes below were
computed at download time:

| File | sha256 (base64) |
| --- | --- |
| `fonts/glyphicons-halflings-regular.eot` | `9JXzTk8XfPARWvmVu7/rP8q8iFAodudvxRpKtDm8hDE=` |
| `fonts/glyphicons-halflings-regular.svg` | `0WjVCojHMLTmgw3A2iorUdrkZYp32WGZQ8J7js/BnRo=` |
| `fonts/glyphicons-halflings-regular.ttf` | `vRjv0+/XD+yK0JYRogzb+ZRAssHUAIXCm+A2+JHWU1g=` |
| `fonts/glyphicons-halflings-regular.woff` | `/Jadwcb/Uxq882gIncuvV3UTOwYm/1a1IwGgWfwPnh4=` |

Licenses and copyright notices: `../LICENSES/`.
