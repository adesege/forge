"""Tests for the completion service."""

from __future__ import annotations

from click.testing import CliRunner

from forge.cli import main
from forge.services import completion


class TestCompletionService:
    """Test the completion service functions directly."""

    def test_bash_completion_script(self):
        result = completion.bash()
        assert "_forge_completion()" in result
        assert "_FORGE_COMPLETE=bash_complete" in result
        assert "complete " in result

    def test_zsh_completion_script(self):
        result = completion.zsh()
        assert "_forge_completion()" in result
        assert "_FORGE_COMPLETE=zsh_complete" in result
        assert "compdef" in result

    def test_fish_completion_script(self):
        result = completion.fish()
        assert "_forge_completion" in result
        assert "_FORGE_COMPLETE=fish_complete" in result
        assert "complete " in result


class TestCompletionCLI:
    """Test the completion CLI commands."""

    def test_completion_bash(self, cli_runner: CliRunner):
        result = cli_runner.invoke(main, ["completion", "bash"])
        assert result.exit_code == 0
        assert "_forge_completion()" in result.output
        assert "_FORGE_COMPLETE=bash_complete" in result.output

    def test_completion_zsh(self, cli_runner: CliRunner):
        result = cli_runner.invoke(main, ["completion", "zsh"])
        assert result.exit_code == 0
        assert "_forge_completion()" in result.output
        assert "compdef" in result.output

    def test_completion_fish(self, cli_runner: CliRunner):
        result = cli_runner.invoke(main, ["completion", "fish"])
        assert result.exit_code == 0
        assert "_forge_completion" in result.output
        assert "_FORGE_COMPLETE=fish_complete" in result.output
