# 4. argparse CLI with config-file precedence

## Status

Accepted

## Context

The CLI needs subcommands (`build`, `serve`), `--help` coverage of
every option (a spec success criterion), and settings that can come
from a config file with CLI-flag overrides (spec Decision 7). The
project ships with zero runtime dependencies; a CLI framework would be
the first one.

Candidates: stdlib `argparse`; `click` (dependency, decorator API,
context objects); `typer` (dependency on click + typing magic). The
surface is two subcommands and under a dozen flags — none of the
framework features (completion tooling, nested groups, prompt helpers)
are needed, and either framework would require an ADR'd runtime
dependency.

## Decision

- Use stdlib `argparse` with subparsers. `main(argv=None) -> int` is
  the single entry point; `UlvError` is caught there and mapped to a
  one-line stderr diagnostic plus exit code 1.
- Settings precedence is **defaults < config file < CLI flags**,
  implemented in `ulv.config`:
  - `Settings` is a flat frozen dataclass; its field list is the single
    source of truth for valid config keys.
  - The config file is TOML (`tomllib`) by default, JSON when the path
    ends in `.json`. `--config` names it explicitly; otherwise
    `./ulv.toml` is used when present. Both parsers are stdlib.
  - Every field has a matching kebab-case flag (`input_format` ↔
    `--input-format`). Flags default to `None` in argparse so an unset
    flag never masks a config-file value.
  - Unknown or non-string config keys raise `UlvError` naming the key
    and file — a typo cannot silently fall back to a default.

## Consequences

- Zero runtime dependencies stands; nothing new to vet or vendor.
- Help texts and flag wiring are written by hand; the Phase 11 help
  audit test asserts every `Settings` field has a flag so the two
  cannot drift apart silently.
- argparse's terse error UX (exit code 2, usage dump) applies to
  syntax-level mistakes; settings-level mistakes get the friendlier
  `UlvError` path.
- Later input formats add their settings as new `Settings` fields plus
  flags, keeping one precedence implementation for every option.
