"""Guards for the harness MCP wiring (stdlib only, no MCP/browser/network).

The Playwright MCP server is configured twice — `.mcp.json` for Claude
Code, `.opencode/opencode.jsonc` for OpenCode — because the two config
formats differ, so version drift between them is the most likely silent
failure. These tests pin both to the same exact version (ADR 0009).
"""

import json
import re
import shutil
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

    def test_input_consuming_hooks_read_through_hook_input(self):
        commands = self._hook_commands()
        for event in ("PreToolUse", "PostToolUse", "Stop"):
            assert any("hook-input.sh" in c for c in commands[event]), (
                f"{event} hook must read its stdin payload via hook-input.sh"
            )

    @pytest.mark.parametrize(
        ("event", "posture"),
        [("PreToolUse", "exit 2"), ("PostToolUse", "exit 1"), ("Stop", "exit 1")],
    )
    def test_hooks_state_a_posture_for_a_missing_parser(self, event, posture):
        # hook-input.sh exits 3 when neither jq nor python3 is on PATH. A hook
        # that does not branch on it inherits whatever the surrounding shell
        # does with an empty read — which is how the guard silently allowed
        # everything before. PreToolUse denies (fail closed); the other two
        # skip with a visible non-zero exit (fail open, but not silently).
        for command in self._hook_commands()[event]:
            if "hook-input.sh" not in command:
                continue
            assert "-eq 3 ]" in command, f"{event} hook ignores hook-input.sh exit 3"
            assert posture in command, (
                f"{event} hook must {posture} when no JSON parser is available"
            )

    def test_pretooluse_matcher_is_anchored_to_bash(self):
        # An unanchored "Bash" also matches BashOutput/KillShell, whose
        # payloads carry no .tool_input.command.
        config = json.loads((REPO_ROOT / ".claude" / "settings.json").read_text())
        matchers = [entry["matcher"] for entry in config["hooks"]["PreToolUse"]]
        assert matchers == ["^Bash$"]


class TestHookInput:
    """Behaviour of the shared hook payload reader.

    Every hook's input now flows through this one script, so its two backends
    must agree: a repo where `jq` is installed and one where only `python3` is
    must give the hooks the same string, or the guard's behaviour depends on
    which machine it runs on. The exit codes are the contract the hooks branch
    on — 3 (no parser) and 4 (bad payload) pick different postures.
    """

    SCRIPT = REPO_ROOT / ".agents" / "hooks" / "hook-input.sh"
    PAYLOAD = json.dumps(
        {
            "tool_input": {"command": 'echo "hi there"', "file_path": "src/a.py"},
            "stop_hook_active": True,
            "nested": {"obj": {"k": 1}},
        }
    )

    def _run(self, path: str, payload: str = PAYLOAD, env=None):
        return subprocess.run(
            ["/bin/sh", str(self.SCRIPT), path],
            input=payload,
            capture_output=True,
            text=True,
            env=env,
        )

    def _restricted_path(self, tmp_path, *tools):
        """A PATH containing only `tools` (plus `cat`, which the script needs)."""
        bin_dir = tmp_path / "bin"
        bin_dir.mkdir()
        for tool in ("cat", *tools):
            source = shutil.which(tool)
            assert source, f"{tool} not found; cannot build a restricted PATH"
            (bin_dir / tool).symlink_to(source)
        return {"PATH": str(bin_dir)}

    @pytest.mark.parametrize(
        ("path", "expected"),
        [
            (".tool_input.command", 'echo "hi there"'),
            (".tool_input.file_path", "src/a.py"),
            (".stop_hook_active", "true"),
            (".missing", ""),
            (".tool_input.command.deeper", ""),
        ],
    )
    def test_reads_fields(self, path, expected):
        result = self._run(path)
        assert result.returncode == 0, result.stderr
        assert result.stdout.strip() == expected

    def test_object_values_come_back_as_json(self):
        result = self._run(".nested.obj")
        assert result.returncode == 0, result.stderr
        assert json.loads(result.stdout) == {"k": 1}

    def test_python_fallback_matches_jq(self, tmp_path):
        # The fallback exists so a jq-less host still gets a working guard;
        # it is only worth having if it returns the same bytes.
        no_jq = self._restricted_path(tmp_path, "python3")
        for path in (".tool_input.command", ".stop_hook_active", ".missing"):
            with_jq = self._run(path)
            without_jq = self._run(path, env=no_jq)
            assert without_jq.returncode == 0, without_jq.stderr
            assert without_jq.stdout == with_jq.stdout, path

    def test_no_parser_exits_3(self, tmp_path):
        result = self._run(".tool_input.command", env=self._restricted_path(tmp_path))
        assert result.returncode == 3
        assert "no working JSON parser" in result.stderr

    @pytest.mark.parametrize("payload", ["", "not json at all"])
    def test_bad_payload_exits_4(self, payload):
        result = self._run(".tool_input.command", payload=payload)
        assert result.returncode == 4, result.stdout
        assert "hook-input.sh:" in result.stderr


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
