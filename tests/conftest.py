"""Shared test fixtures for forge."""

from __future__ import annotations

import importlib
from unittest.mock import MagicMock

import pytest
from click.testing import CliRunner
from click_clop.service import ServiceRegistry

from forge.services import auth as _auth_mod
from forge.services import completion as _completion_mod
from forge.services import issue as _issue_mod
from forge.services import org as _org_mod
from forge.services import package as _package_mod
from forge.services import pr as _pr_mod
from forge.services import release as _release_mod
from forge.services import repo as _repo_mod

_SERVICE_MODULES = [
    _auth_mod,
    _completion_mod,
    _issue_mod,
    _org_mod,
    _package_mod,
    _pr_mod,
    _release_mod,
    _repo_mod,
]


@pytest.fixture(autouse=True)
def _reset_registry() -> None:  # type: ignore[misc]
    """Reset the service registry between tests."""
    ServiceRegistry.reset()
    for mod in _SERVICE_MODULES:
        importlib.reload(mod)
    yield  # type: ignore[misc]
    ServiceRegistry.reset()


@pytest.fixture
def cli_runner() -> CliRunner:
    """Click CLI test runner."""
    return CliRunner()


@pytest.fixture
def mock_forgejo_client() -> MagicMock:  # type: ignore[misc]
    """Provide a mock ForgejoClient and patch get_client to return it.

    Sets the module-level _client cache so get_client() returns the mock
    without trying to load config or resolve tokens.
    """
    import forge.forgejo.client as client_mod

    mock_client = MagicMock()
    original = client_mod._client
    client_mod._client = mock_client
    yield mock_client  # type: ignore[misc]
    client_mod._client = original
