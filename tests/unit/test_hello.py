"""Tests for the hello service."""

from __future__ import annotations

from click.testing import CliRunner
from click_clop.service import ServiceRegistry

from forge.cli import main


class TestHelloService:
    """Test the HelloService methods directly."""

    def test_greet_default(self):
        svc = ServiceRegistry.get().get_service("hello")
        assert svc is not None
        greet = next(m for m in svc.methods() if m.name == "greet")
        assert greet.func() == "Hello, world!"

    def test_greet_with_name(self):
        svc = ServiceRegistry.get().get_service("hello")
        assert svc is not None
        # Find the greet method
        greet = next(m for m in svc.methods() if m.name == "greet")
        assert greet.func(name="Claude") == "Hello, Claude!"

    def test_farewell(self):
        svc = ServiceRegistry.get().get_service("hello")
        assert svc is not None
        farewell = next(m for m in svc.methods() if m.name == "farewell")
        assert farewell.func(name="Claude") == "Goodbye, Claude!"


class TestHelloCLI:
    """Test the hello CLI commands."""

    def test_hello_greet(self, cli_runner: CliRunner):
        result = cli_runner.invoke(main, ["hello", "greet", "--name", "World"])
        assert result.exit_code == 0
        assert "Hello, World!" in result.output

    def test_hello_farewell(self, cli_runner: CliRunner):
        result = cli_runner.invoke(main, ["hello", "farewell", "--name", "World"])
        assert result.exit_code == 0
        assert "Goodbye, World!" in result.output
