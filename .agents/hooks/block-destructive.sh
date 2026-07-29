#!/usr/bin/env sh
# block-destructive.sh — canonical destructive-command matcher.
#
# Reads candidate command text on stdin; exits 2 (with a message naming the
# deny-list, so a deny is distinguishable from an infrastructure failure) if it
# matches a forbidden pattern, 0 otherwise. This is the single source of truth
# for the deny-list.
#
# The deny decision deliberately stays on POSIX `grep -qE`: extracting the
# matched pattern with `grep -o` would make the decision depend on a non-POSIX
# extension that also suppresses stdout on binary-classified input, silently
# failing open in both cases.
#
# Consumers:
#   - Claude Code: the PreToolUse(Bash) hook in .claude/settings.json pipes the
#     tool input here.
#   - OpenCode: cannot call a script, so the deny globs in
#     .opencode/opencode.jsonc restate these patterns by hand — keep in sync.
#
# See .agents/README.md for the single-source-of-truth rationale.
if grep -qE 'rm -rf|push --force|reset --hard|DROP TABLE'; then
	echo 'block-destructive: denied - the command matches the destructive deny-list (rm -rf, push --force, reset --hard, DROP TABLE).' >&2
	exit 2
fi
exit 0
