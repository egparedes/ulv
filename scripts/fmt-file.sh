#!/usr/bin/env bash
# fmt-file.sh — per-file formatter, invoked by the Claude Code
# PostToolUse hook after Write/Edit/MultiEdit with the edited file as $1,
# and by OpenCode's `formatter` entry in .opencode/opencode.jsonc.
# Keep this fast (<300ms); it runs on every save.
#
# Formatting must be byte-for-byte what `make verify` enforces
# (`uv run ruff format --check .`), so both go through ruff with the same
# pyproject configuration — including its extend-exclude list, which ruff
# applies itself when given an explicit path only if we pass --force-exclude.

set -euo pipefail

file="${1:-}"
[[ -z "$file" ]] && { echo "usage: $0 <file>" >&2; exit 64; }

# Nothing to do for a path that vanished between the edit and this hook.
[[ -f "$file" ]] || exit 0

case "$file" in
*.py | *.pyi) ;;
*) exit 0 ;;
esac

# `uv run` without a network or a synced venv would stall the agent loop;
# skip rather than block. The gate still catches unformatted code.
command -v uv >/dev/null 2>&1 || exit 0

# --force-exclude makes ruff honour pyproject's extend-exclude for an
# explicitly-named file, so vendored trees are left alone here exactly as
# they are by `make fmt`. Failure is never fatal: a syntax error mid-edit
# is the agent's problem to fix, not this hook's to report.
uv run --quiet ruff format --force-exclude "$file" >/dev/null 2>&1 || true
