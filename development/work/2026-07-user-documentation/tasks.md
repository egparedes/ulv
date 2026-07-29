# Tasks

## Phase 1 — Directory scaffold and quickstart

- [x] Create `docs/user/index.md` with intro and table of contents
- [x] Create `docs/user/quickstart.md` with prerequisites, clone, install, build, serve steps
- [x] Manually verify quickstart commands run successfully

## Phase 2 — ASV format guide

- [x] Create `docs/user/asv.md` covering directory layout
- [x] Document minimal `ulv build -i asv` invocation
- [x] Document `--project` option
- [x] Document git enrichment: `--repo`, `--branches`, `--show-commit-url`
- [x] Verify example commands run against `tests/fixtures/asv_results/`

## Phase 3 — BMF format guide with dedicated sample

- [x] Create `docs/user/samples/bmf/` directory
- [x] Add 2-3 sample BMF `.json` files
- [x] Add `docs/user/samples/bmf/manifest.json`
- [x] Create `docs/user/bmf.md` covering BMF structure
- [x] Document single-file invocation with `--commit`, `--date`, `--testbed`
- [x] Document multi-file with `--manifest`
- [x] Document multi-file with `--filename-pattern`
- [x] Verify example commands run against samples

## Phase 4 — Bencher API guide

- [x] Create `docs/user/bencher-api.md`
- [x] Document `--bencher-project` requirement
- [x] Document `--bencher-url` for self-hosted instances
- [x] Document authentication via `BENCHER_API_TOKEN` and `--bencher-token`
- [x] Add placeholder project slug with substitution instructions

## Phase 5 — Config file and testbed decomposition guide

- [x] Create `docs/user/config.md` covering config file discovery
- [x] Document `--config FILE` option
- [x] Document precedence: defaults < config < flags
- [x] List all config keys with descriptions
- [x] Add example `ulv.toml` for ASV project
- [x] Create `docs/user/testbeds.md` covering `[testbeds]` table
- [x] Document `--testbeds-file` option
- [x] Document `--allow-unmapped` option
- [x] Add example decomposing testbeds into factors

## Phase 6 — CLI reference

- [x] Create `docs/user/cli-reference.md`
- [x] Document `ulv --version` and `ulv --help`
- [x] Document all `ulv build` flags with types and defaults
- [x] Document all `ulv serve` flags with types and defaults
- [x] Cross-check against `--help` output for completeness

## Phase 7 — Verification tests for documentation

- [x] Create `tests/test_docs.py`
- [x] Add test for quickstart command against ASV fixture
- [x] Add test for BMF sample command
- [x] Add test for config file parsing
- [x] Verify `make verify` passes with new tests

## Phase 8 — Index, cross-links, and polish

- [x] Update `docs/user/index.md` with complete table of contents
- [x] Add navigation links to each page
- [x] Review all pages for consistent style per `docs/style.md`
- [x] Verify no broken internal links
- [x] Final `make verify` pass

## Phase 9 — Add Zensical as dev dependency

- [x] Add `zensical` to the `dev` dependency group in `pyproject.toml`
- [x] Run `uv sync` to verify the dependency resolves
- [x] Verify Zensical CLI is available in the dev environment

## Phase 10 — Zensical configuration

- [x] Research Zensical configuration format from installed package
- [x] Create Zensical configuration file with source/output directories
- [x] Configure site title and navigation structure
- [x] Add output directory to `.gitignore`
- [x] Run Zensical build and verify site generation

## Phase 11 — Auto-generated CLI reference

- [x] Research Zensical argparse introspection mechanism
- [x] Configure Zensical to extract CLI docs from `ulv.cli:build_parser`
- [x] Configure output location for generated CLI reference
- [x] Preserve hand-written prose sections (examples, env vars, see-also)
- [x] Remove or archive hand-written `cli-reference.md` if replaced
- [x] Verify generated reference includes all commands, options, types, defaults

## Phase 12 — Auto-generated API reference

- [x] Research Zensical API documentation mechanism
- [x] Configure Zensical to document `ulv.model` public classes
- [x] Configure Zensical to document `ulv.config` public classes/functions
- [x] Configure Zensical to document `ulv.errors` public classes
- [x] Configure Zensical to document `ulv.testbeds` public classes/functions
- [x] Configure Zensical to document `ulv.plugins` protocols and registries
- [x] Exclude internal/private members from documentation
- [x] Verify generated reference includes docstrings and type hints

## Phase 13 — Makefile integration

- [x] Add `make docs` target with `uv run zensical build`
- [x] Add help comment for `make docs`
- [x] Add `make docs-serve` target with `uv run zensical serve`
- [x] Add help comment for `make docs-serve`
- [x] Add both targets to `.PHONY` declaration
- [x] Verify `make help` shows new targets

## Phase 14 — Staleness checks in verify

- [x] Research Zensical staleness checking mechanism
- [x] Add `make docs-check` target for staleness validation
- [x] Add help comment for `make docs-check`
- [x] Integrate `docs-check` into `scripts/verify.sh`
- [x] Verify staleness check fails when source changes without rebuild

## Phase 15 — Final integration and cleanup

- [x] Run full `make verify` with all checks
- [x] Build complete documentation site with `make docs`
- [x] Manual review: navigation works correctly
- [x] Manual review: CLI reference is complete and accurate
- [x] Manual review: API reference documents all public modules
- [x] Manual review: cross-links between pages work
- [x] Update `docs/user/index.md` with API reference links if needed
- [x] Confirm all spec criteria 8-15 satisfied
