"""Step definitions for the repo clone feature."""

from unittest.mock import MagicMock, patch

from behave import given, use_step_matcher

import forge.forgejo.client as client_mod

use_step_matcher("parse")


@given('a mock Forgejo repo "{full_name}" with clone URL "{clone_url}"')
def step_mock_repo(context, full_name, clone_url):
    mock_client = MagicMock()
    mock_client.get.return_value = {
        "full_name": full_name,
        "clone_url": clone_url,
    }
    context._original_client = client_mod._client
    client_mod._client = mock_client

    mock_run = patch("forge.services.repo.subprocess.run")
    context._mock_run = mock_run.start()
    context._mock_run.return_value = MagicMock(returncode=0)
    context._mock_run_patcher = mock_run

    def cleanup():
        client_mod._client = context._original_client
        mock_run.stop()

    context.add_cleanup(cleanup)


@given("an empty Forgejo repo list")
def step_empty_repo_list(context):
    mock_client = MagicMock()
    mock_client.get.return_value = []
    context._original_client = client_mod._client
    client_mod._client = mock_client

    def cleanup():
        client_mod._client = context._original_client

    context.add_cleanup(cleanup)
