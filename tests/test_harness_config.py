"""Guards for the harness MCP wiring (stdlib only, no MCP/browser/network).

The Playwright MCP server is configured twice — `.mcp.json` for Claude
Code, `.opencode/opencode.jsonc` for OpenCode — because the two config
formats differ, so version drift between them is the most likely silent
failure. These tests pin both to the same exact version (ADR 0009).
"""

import json
import re
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).parent.parent

# The single source of truth for the pinned server version; bumping it
# means editing both config files and this constant in one commit.
PINNED_SERVER = "@playwright/mcp@0.0.78"

REQUIRED_FLAGS = {"--headless", "--isolated", "--caps=vision", "--browser"}

# The server default is chrome-for-testing; we pin the Playwright-bundled
# chromium so the SKILL's `npx playwright install chromium` step matches.
PINNED_BROWSER = "chromium"


class TestClaudeCodeMcpConfig:
    def _args(self):
        config = json.loads((REPO_ROOT / ".mcp.json").read_text())
        return config["mcpServers"]["playwright"]["args"]

    def test_pins_exact_server_version(self):
        args = self._args()
        assert PINNED_SERVER in args
        assert not any("@latest" in arg for arg in args)

    def test_required_flags_present(self):
        args = self._args()
        assert REQUIRED_FLAGS <= set(args)
        browser_value = args.index("--browser") + 1
        assert browser_value < len(args), "--browser must be followed by a value"
        assert args[browser_value] == PINNED_BROWSER

    def test_runs_via_npx(self):
        config = json.loads((REPO_ROOT / ".mcp.json").read_text())
        assert config["mcpServers"]["playwright"]["command"] == "npx"


class TestOpenCodeMcpConfig:
    def _command(self):
        # opencode.jsonc has comments, so it isn't valid JSON; rather than
        # scan the whole file (where a pin mentioned only in a comment would
        # pass), isolate the playwright MCP command array by shape and check
        # the pins inside the actual invocation. Substring checks within the
        # array stay tolerant of formatting churn.
        text = (REPO_ROOT / ".opencode" / "opencode.jsonc").read_text()
        match = re.search(
            r'"playwright"\s*:\s*\{.*?"command"\s*:\s*\[(.*?)\]',
            text,
            re.DOTALL,
        )
        assert match, "playwright MCP command array not found in opencode.jsonc"
        return match.group(1)

    def test_same_pinned_version_in_lockstep(self):
        assert PINNED_SERVER in self._command()
        # a stray @latest anywhere in the file is a red flag regardless of block
        assert (
            "@playwright/mcp@latest"
            not in (REPO_ROOT / ".opencode" / "opencode.jsonc").read_text()
        )

    def test_required_flags_present(self):
        command = self._command()
        for flag in REQUIRED_FLAGS:
            assert flag in command, flag
        assert PINNED_BROWSER in command


class TestClaudeCodeHookWiring:
    """Pin how the hooks read their input.

    The template shipped these hooks reading `$CLAUDE_TOOL_INPUT` and
    `$CLAUDE_TOOL_INPUT_FILE_PATH`, variables Claude Code never sets. The
    destructive-command guard therefore matched an empty string and allowed
    every command for the whole life of that template version, with nothing
    to notice. These tests fail if the stdin plumbing regresses that way
    again — a `copier update` or a merge is enough to do it.
    """

    def _hook_commands(self) -> dict[str, list[str]]:
        config = json.loads((REPO_ROOT / ".claude" / "settings.json").read_text())
        return {
            event: [h["command"] for entry in entries for h in entry["hooks"]]
            for event, entries in config["hooks"].items()
        }

    def test_no_hook_reads_the_never_set_env_vars(self):
        for event, commands in self._hook_commands().items():
            for command in commands:
                assert "CLAUDE_TOOL_INPUT" not in command, (
                    f"{event} hook reads $CLAUDE_TOOL_INPUT*, which Claude Code "
                    f"never sets; parse the stdin JSON instead"
                )

    def test_input_consuming_hooks_parse_stdin(self):
        commands = self._hook_commands()
        for event in ("PreToolUse", "PostToolUse", "Stop"):
            assert any("jq" in c for c in commands[event]), (
                f"{event} hook must parse its stdin JSON payload"
            )

    def test_hooks_degrade_when_jq_is_absent(self):
        # jq is a system package nothing in this repo installs. A hook that
        # fails closed on a missing jq bricks every Bash call in the session.
        for event, commands in self._hook_commands().items():
            for command in commands:
                if "jq" not in command:
                    continue
                assert "command -v jq" in command, (
                    f"{event} hook uses jq without checking it exists first"
                )

    def test_pretooluse_matcher_is_anchored_to_bash(self):
        # An unanchored "Bash" also matches BashOutput/KillShell, whose
        # payloads carry no .tool_input.command.
        config = json.loads((REPO_ROOT / ".claude" / "settings.json").read_text())
        matchers = [entry["matcher"] for entry in config["hooks"]["PreToolUse"]]
        assert matchers == ["^Bash$"]


class TestBlockDestructive:
    """Behaviour of the shared deny-list matcher.

    Exit 2 means blocked, 0 means allowed. The allow cases matter as much as
    the block cases: the matcher runs on every Bash call, and one that trips
    on a command merely *quoting* a pattern (`rg "<pattern>" .agents/`) makes
    the agent loop unusable.
    """

    SCRIPT = REPO_ROOT / ".agents" / "hooks" / "block-destructive.sh"

    def _run(self, command: str) -> subprocess.CompletedProcess:
        return subprocess.run(
            ["sh", str(self.SCRIPT)],
            input=command,
            capture_output=True,
            text=True,
        )

    # Spelled via .format() so the literal patterns never appear in this
    # file's own source: an agent grepping the test suite would otherwise
    # trip the very guard under test.
    RECURSIVE_DELETE = "{} -{}".format("rm", "rf")
    FORCE_PUSH = "git push --{}".format("force")
    HARD_RESET = "git reset --{}".format("hard")

    @pytest.mark.parametrize(
        "command",
        [
            f"{RECURSIVE_DELETE} /data",
            "{} -{} /data".format("rm", "fr"),
            "{}  -{} /data".format("rm", "rf"),
            "{} -r -f /data".format("rm"),
            f"sudo {RECURSIVE_DELETE} /data",
            f"cd /tmp && {RECURSIVE_DELETE} build",
            f"{FORCE_PUSH} origin main",
            f"git -C /repo push --{'force'} origin main",
            f"{HARD_RESET} origin/main",
            'psql -c "{} users"'.format("DROP TABLE"),
        ],
    )
    def test_blocks_destructive_commands(self, command):
        result = self._run(command)
        assert result.returncode == 2, f"should have blocked: {command!r}"

    def test_a_block_explains_itself(self):
        # An exit 2 with no stderr reaches the agent as a bare "hook error",
        # indistinguishable from broken tooling, so it retries the command.
        result = self._run(f"{self.RECURSIVE_DELETE} /data")
        assert "block-destructive:" in result.stderr

    @pytest.mark.parametrize(
        "command",
        [
            f'rg "{RECURSIVE_DELETE}" .agents/',
            f"rg '{RECURSIVE_DELETE}' .agents/",
            f'git log --grep="{HARD_RESET[4:]}"',
            f'echo "never run {RECURSIVE_DELETE} on a shared tree"',
            "{} /tmp/one-file".format("rm"),
            "{} -r build".format("rm"),
            "{} -f stale.lock".format("rm"),
            "git push origin main",
            "git push --force-with-lease origin feat",
            "git reset --soft HEAD~1",
            "make verify",
            "",
        ],
    )
    def test_allows_benign_commands(self, command):
        result = self._run(command)
        assert result.returncode == 0, (
            f"should have allowed: {command!r} (stderr: {result.stderr})"
        )


class TestUiParityCheckSkill:
    def test_skill_file_exists_with_frontmatter(self):
        skill = REPO_ROOT / ".agents" / "skills" / "ui-parity-check" / "SKILL.md"
        text = skill.read_text()
        frontmatter = re.match(r"---\n(.*?)\n---\n", text, re.DOTALL)
        assert frontmatter, "SKILL.md must start with YAML frontmatter"
        assert re.search(r"^name: ui-parity-check$", frontmatter.group(1), re.M)
        assert re.search(r"^description:", frontmatter.group(1), re.M)
