"""Help completeness audit (spec: --help documents every command and
option; every documented invocation works)."""

import re
import shlex
from dataclasses import fields
from pathlib import Path

import pytest

from ulv.cli import build_parser, main
from ulv.config import Settings

DOCS = [
    Path(__file__).parent.parent / "development" / "architecture.md",
    Path(__file__).parent.parent / "CHANGELOG.md",
]

# Settings fields whose flag spelling is not the mechanical kebab-case
# derivation: the structured [testbeds] table is supplied via a file,
# and the output generator keeps the shorter --generator spelling.
MAPPED_FLAGS = {"testbeds": "--testbeds-file", "output_generator": "--generator"}


def _subparser(name: str):
    parser = build_parser()
    for action in parser._actions:
        if hasattr(action, "choices") and isinstance(action.choices, dict):
            return action.choices[name]
    raise AssertionError("no subparsers found")


class TestFlagCoverage:
    def test_every_settings_field_has_a_build_flag(self):
        build = _subparser("build")
        option_strings = {
            option for action in build._actions for option in action.option_strings
        }
        for field in fields(Settings):
            flag = MAPPED_FLAGS.get(field.name, "--" + field.name.replace("_", "-"))
            assert flag in option_strings, (field.name, flag)

    @pytest.mark.parametrize("command", ["build", "serve"])
    def test_every_option_has_help_text(self, command):
        for action in _subparser(command)._actions:
            assert action.help, action.option_strings or action.dest


class TestBareInvocation:
    def test_bare_ulv_prints_help(self, capsys):
        rc = main([])
        assert rc == 0
        out = capsys.readouterr().out
        assert "usage" in out.lower()
        assert "build" in out
        assert "serve" in out


class TestDocumentedInvocations:
    def _documented_commands(self):
        commands = []
        for doc in DOCS:
            for line in doc.read_text().splitlines():
                stripped = line.strip()
                if stripped.startswith("ulv "):
                    commands.append(stripped)
        return commands

    def test_docs_contain_example_invocations(self):
        assert len(self._documented_commands()) >= 3

    def test_every_documented_invocation_parses(self):
        parser = build_parser()
        for command in self._documented_commands():
            argv = shlex.split(re.sub(r"\s+#.*$", "", command))[1:]
            try:
                parser.parse_args(argv)
            except SystemExit as exc:
                raise AssertionError(f"documented invocation fails: {command}") from exc
