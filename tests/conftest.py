"""Shared test fixtures for forge."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from forge.forgejo import client as client_mod


@pytest.fixture(autouse=True)
def _reset_client():
    """Reset the Forgejo client singleton between tests."""
    client_mod._client = None
    yield
    client_mod._client = None


@pytest.fixture
def mock_forgejo_client():
    """Provide a mock ForgejoClient patched into the module-level singleton."""
    mock = MagicMock()
    with patch.object(client_mod, "_client", mock):
        yield mock


@pytest.fixture
def cli_runner():
    """Click CLI test runner."""
    return CliRunner()
