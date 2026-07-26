#!/usr/bin/env sh
# block-destructive.sh — canonical destructive-command matcher.
#
# Reads candidate command text on stdin; exits 2 (with a reason on stderr) if
# it matches a forbidden pattern, 0 otherwise. This is the single source of
# truth for the deny-list.
#
# Consumers:
#   - Claude Code: the PreToolUse(Bash) hook in .claude/settings.json pipes the
#     tool input here.
#   - OpenCode: cannot call a script, so the deny globs in
#     .opencode/opencode.jsonc restate these patterns by hand — keep in sync.
#     Those globs are plain substring matches and cannot express the quoting
#     and command-position rules below, so OpenCode over-blocks where this
#     script does not.
#
# See .agents/README.md for the single-source-of-truth rationale.

cmd=$(cat)
[ -n "$cmd" ] || exit 0

# Shell-syntax patterns are matched against text with quoted spans removed, so
# a command that merely *names* a dangerous form — `rg "rm -rf" .agents/`,
# `git log --grep="reset --hard"`, a heredoc documenting the deny-list — is not
# blocked. Only an unquoted occurrence is shell the caller is about to run.
bare=$(printf '%s' "$cmd" | sed -e "s/'[^']*'/''/g" -e 's/"[^"]*"/""/g')

deny() {
	printf 'block-destructive: refusing this command — %s.\n' "$1" >&2
	printf 'block-destructive: %s\n' "$cmd" >&2
	printf 'block-destructive: see .agents/hooks/block-destructive.sh for the deny-list.\n' >&2
	exit 2
}

# A command position: start of input, or after a separator that begins a new
# command. Keeps `rm` as an argument (`git log -- rm`) from matching.
POS='(^|[;&|(]|\$\()[[:space:]]*(sudo[[:space:]]+)?'

# Recursive *and* forced delete, in the spellings that actually occur:
# combined (-rf, -fr, -rvf), separate (-r -f, -f -r), and long-form.
match() { printf '%s' "$bare" | grep -qE "$1"; }

match "${POS}rm[[:space:]]+(-[A-Za-z]+[[:space:]]+)*-[A-Za-z]*([rR][A-Za-z]*[fF]|[fF][A-Za-z]*[rR])" ||
	match "${POS}rm[[:space:]]+(-[A-Za-z]*[rR][A-Za-z]*[[:space:]]+)+(-[A-Za-z]*[fF])" ||
	match "${POS}rm[[:space:]]+(-[A-Za-z]*[fF][A-Za-z]*[[:space:]]+)+(-[A-Za-z]*[rR])" ||
	match "${POS}rm([[:space:]]+--(recursive|force))+[[:space:]]+--(recursive|force)" &&
	deny 'a recursive forced delete'

# `[^;&|()]*` spans git's own options (`git -C /repo push …`) without running
# past the end of the command. `--force([^-]|$)` leaves --force-with-lease,
# the reviewable form, allowed.
match "${POS}git[[:space:]]+([^;&|()]*[[:space:]]+)?push[[:space:]]+[^;&|()]*--force([^-]|\$)" &&
	deny 'a force push (use --force-with-lease on your own branch, deliberately)'

match "${POS}git[[:space:]]+([^;&|()]*[[:space:]]+)?reset[[:space:]]+[^;&|()]*--hard" &&
	deny 'a hard reset (it discards uncommitted work irreversibly)'

# SQL, unlike the above, is normally *inside* quotes (`psql -c "DROP TABLE x"`),
# so this one is matched against the raw text.
printf '%s' "$cmd" | grep -qiE 'DROP[[:space:]]+(TABLE|DATABASE|SCHEMA)' &&
	deny 'a destructive SQL statement'

exit 0
