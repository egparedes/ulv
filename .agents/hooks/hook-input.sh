#!/usr/bin/env sh
# hook-input.sh — canonical reader for agent-hook JSON payloads.
#
# Usage: hook-input.sh <dot.path>       (stdin: the hook's JSON payload)
#   e.g. hook-input.sh .tool_input.command
#
# Prints the field's value on stdout, identically under either backend:
# '' for null/absent (including a path through a non-object), 'true'/'false'
# for booleans, raw text for strings and numbers, JSON for objects/arrays.
#
# Exit codes: 0 read OK; 3 no working JSON parser on PATH; 4 empty or
# unparseable payload. Callers branch on the distinction to pick their own
# failure posture and message.
#
# Parses with jq when available, falling back to python3. The fallback is
# probed by *running* python3, not `command -v` alone — stock macOS ships a
# /usr/bin/python3 stub that passes `command -v` but fails until the Xcode
# Command Line Tools are installed.
#
# Consumers:
#   - Claude Code: the PostToolUse, PreToolUse, and Stop hooks in
#     .claude/settings.json read their payloads through this script.
#
# See .agents/README.md for the single-source-of-truth rationale.

payload=$(cat)
if [ -z "$payload" ]; then
	echo 'hook-input.sh: empty hook payload on stdin.' >&2
	exit 4
fi

if command -v jq >/dev/null 2>&1; then
	out=$(printf '%s' "$payload" | jq -r --arg p "$1" '
		($p | split(".") | map(select(length > 0))) as $parts
		| (try getpath($parts) catch null)
		| if . == null then "" elif type == "boolean" then tostring else . end
	' 2>/dev/null) || {
		echo 'hook-input.sh: cannot parse the hook payload as JSON.' >&2
		exit 4
	}
	printf '%s\n' "$out"
	exit 0
fi

if python3 -c '' >/dev/null 2>&1; then
	printf '%s' "$payload" | python3 -c '
import json, sys
try:
    v = json.load(sys.stdin)
except ValueError:
    print("hook-input.sh: cannot parse the hook payload as JSON.", file=sys.stderr)
    sys.exit(4)
for p in [p for p in sys.argv[1].split(".") if p]:
    v = v.get(p) if isinstance(v, dict) else None
if v is None:
    print("")
elif v is True or v is False:
    print(str(v).lower())
elif isinstance(v, (dict, list)):
    print(json.dumps(v))
else:
    print(v)
' "$1"
	exit $?
fi

echo 'hook-input.sh: no working JSON parser (jq or python3) on PATH; cannot read the hook input. Install jq (apt-get install jq / brew install jq).' >&2
exit 3
