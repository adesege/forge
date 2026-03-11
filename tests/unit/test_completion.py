"""Tests for the completion service."""

from __future__ import annotations

from click.testing import CliRunner
from click_clop.service import ServiceRegistry

from forge.cli import main


class TestCompletionService:
    """Test the CompletionService methods directly."""

    def test_bash_completion_script(self):
        svc = ServiceRegistry.get().get_service("completion")
        assert svc is not None
        bash = next(m for m in svc.methods() if m.name == "bash")
        result = bash.func()
        assert "_forge_completion()" in result
        assert "_FORGE_COMPLETE=bash_complete" in result
        assert "complete " in result

    def test_zsh_completion_script(self):
        svc = ServiceRegistry.get().get_service("completion")
        assert svc is not None
        zsh = next(m for m in svc.methods() if m.name == "zsh")
        result = zsh.func()
        assert "_forge_completion()" in result
        assert "_FORGE_COMPLETE=zsh_complete" in result
        assert "compdef" in result

    def test_fish_completion_script(self):
        svc = ServiceRegistry.get().get_service("completion")
        assert svc is not None
        fish = next(m for m in svc.methods() if m.name == "fish")
        result = fish.func()
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
