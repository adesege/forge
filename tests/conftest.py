"""Shared test fixtures for forge."""

from __future__ import annotations

import importlib

import pytest
from click.testing import CliRunner
from click_clop.service import ServiceRegistry

from forge.services import hello as _hello_mod


@pytest.fixture(autouse=True)
def _reset_registry():
    """Reset the service registry between tests."""
    ServiceRegistry.reset()
    # Reload to re-execute module-level auto-registration
    importlib.reload(_hello_mod)
    yield
    ServiceRegistry.reset()


@pytest.fixture
def cli_runner():
    """Click CLI test runner."""
    return CliRunner()
