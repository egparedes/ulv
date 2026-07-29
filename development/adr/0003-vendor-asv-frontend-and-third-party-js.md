# 3. Vendor the ASV web frontend and its third-party JS/CSS

## Status

Accepted

## Context

The spec reuses ASV's browsing UI for v1 (spec Decision 2) and requires
the generated site to perform no network requests beyond fetching its
own static files. ASV's `index.html` loads jQuery, flot (+plugins),
flot-orderbars, stupidtable, blueimp-md5 and Bootstrap from CDNs with
pinned versions and subresource-integrity hashes; everything else in
`asv/www/` is local. We need those assets inside the `ulv` package so a
generated site is self-contained, and we must not ship ASV's
regressions page (regression detection is out of scope, spec
Decision 6).

Licensing: ASV is BSD-3-Clause; the CDN libraries are MIT (jQuery,
flot, flot-orderbars, stupidtable, blueimp-md5, Bootstrap 3). All
permit redistribution with attribution and license text.

## Decision

- Copy `external/asv/asv/www/` into `src/ulv/outputs/html/static/`,
  excluding `regressions.js` and `regressions.css`. The already-local
  `jquery.flot.axislabels.js` is kept as-is.
- Download each CDN asset once, at the exact URL pinned in ASV's
  `index.html`, verify it against the integrity hash from that file
  (sha256/sha512, base64), and commit it under `static/vendor/`.
  Bootstrap's glyphicon font files (referenced relatively by
  `bootstrap.min.css` from the same bootstrap@3.1.1 distribution) are
  vendored alongside so the site resolves every reference locally.
- Patch policy: minimal, removals over edits, every patch recorded in
  `src/ulv/outputs/html/VENDORED.md` together with the upstream ASV
  commit and the vendored library versions/hashes. Patches at
  vendoring time: point `index.html` script/link tags at
  `vendor/…` relative paths, and remove the regressions nav item,
  display div, script/css tags and the atom-feed link.
- Attribution: `src/ulv/outputs/html/LICENSES/` carries one file per
  component with its license text and copyright. The directory ships
  in the wheel with the rest of the package.

## Consequences

- Generated sites are fully self-contained; the no-network criterion
  is testable by scanning emitted assets for absolute URLs.
- We take on ~1 MB of committed third-party assets and the duty to
  keep `VENDORED.md` honest when anything under `static/` changes.
- Upstream ASV frontend fixes do not arrive automatically; refreshing
  means re-vendoring against a newer ASV commit and re-applying the
  recorded patches.
- The frontend contract (`index.json` shape, `graphs/…` file paths)
  is pinned to the vendored commit, which is what the generator's
  path-compatibility tests are written against.
