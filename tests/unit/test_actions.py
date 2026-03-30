"""Tests for the actions service."""

from __future__ import annotations

from unittest.mock import patch

from forge.services import actions


class TestListRuns:
    """Tests for list_runs."""

    def test_list_runs(self, mock_forgejo_client) -> None:  # type: ignore[no-untyped-def]
        mock_forgejo_client.get.return_value = {
            "workflow_runs": [
                {
                    "index_in_repo": 1,
                    "status": "success",
                    "title": "CI",
                    "event": "push",
                    "commit_sha": "abc123",
                    "started": "2026-01-01T00:00:00Z",
                },
            ],
        }
        result = actions.list_runs(owner="o", repo="r")
        assert "CI" in result

    def test_list_runs_empty(self, mock_forgejo_client) -> None:  # type: ignore[no-untyped-def]
        mock_forgejo_client.get.return_value = {"workflow_runs": []}
        result = actions.list_runs(owner="o", repo="r")
        assert "No action runs found" in result

    def test_list_runs_with_filters(self, mock_forgejo_client) -> None:  # type: ignore[no-untyped-def]
        mock_forgejo_client.get.return_value = {"workflow_runs": []}
        actions.list_runs(owner="o", repo="r", status="success", event="push")
        mock_forgejo_client.get.assert_called_once()
        call_params = mock_forgejo_client.get.call_args
        assert "status" in str(call_params)

    def test_list_runs_infers_context(self, mock_forgejo_client) -> None:  # type: ignore[no-untyped-def]
        mock_forgejo_client.get.return_value = {"workflow_runs": []}
        with patch("forge.services.actions.get_repo_context", return_value=("o", "r")):
            result = actions.list_runs()
            assert "No action runs found" in result

    def test_list_runs_flat_response(self, mock_forgejo_client) -> None:  # type: ignore[no-untyped-def]
        """Handle response that is a plain list instead of dict with workflow_runs."""
        mock_forgejo_client.get.return_value = [
            {
                "index_in_repo": 1,
                "status": "success",
                "title": "CI",
                "event": "push",
                "commit_sha": "abc123",
                "started": "2026-01-01T00:00:00Z",
            },
        ]
        result = actions.list_runs(owner="o", repo="r")
        assert "CI" in result


class TestViewRun:
    """Tests for view_run."""

    def test_view_run(self, mock_forgejo_client) -> None:  # type: ignore[no-untyped-def]
        mock_forgejo_client.get.return_value = {
            "id": 38,
            "index_in_repo": 5,
            "title": "CI Pipeline",
            "status": "success",
            "event": "push",
            "workflow_id": "ci.yml",
            "prettyref": "main",
            "commit_sha": "abc123def456",
            "trigger_user": {"login": "dev"},
            "started": "2026-01-01T00:00:00Z",
            "stopped": "2026-01-01T00:05:00Z",
            "html_url": "https://example.com/o/r/actions/runs/38",
        }
        result = actions.view_run(run_id=38, owner="o", repo="r")
        assert "CI Pipeline" in result
        assert "success" in result

    def test_view_run_no_id(self) -> None:
        result = actions.view_run(owner="o", repo="r")
        assert "Error" in result

    def test_view_run_infers_context(self, mock_forgejo_client) -> None:  # type: ignore[no-untyped-def]
        mock_forgejo_client.get.return_value = {
            "id": 1,
            "index_in_repo": 1,
            "title": "CI",
            "status": "running",
            "event": "push",
            "workflow_id": "ci.yml",
            "prettyref": "main",
            "commit_sha": "abc123",
            "trigger_user": {"login": "u"},
            "started": "2026-01-01",
            "stopped": "",
        }
        with patch("forge.services.actions.get_repo_context", return_value=("o", "r")):
            result = actions.view_run(run_id=1)
            assert "CI" in result


class TestLog:
    """Tests for log."""

    def test_log_no_run_id(self) -> None:
        result = actions.log(owner="o", repo="r")
        assert "Error" in result

    def test_log_with_data(self, mock_forgejo_client) -> None:  # type: ignore[no-untyped-def]
        mock_forgejo_client.post_web.return_value = {
            "logs": {
                "2": {
                    "lines": [
                        {"message": "Step started"},
                        {"message": "Running tests..."},
                        {"message": "All tests passed"},
                    ],
                },
            },
        }
        result = actions.log(run_id=38, job=0, step=2, owner="o", repo="r")
        assert "Running tests" in result
        assert "All tests passed" in result

    def test_log_no_data(self, mock_forgejo_client) -> None:  # type: ignore[no-untyped-def]
        mock_forgejo_client.post_web.return_value = None
        result = actions.log(run_id=38, owner="o", repo="r")
        assert "No log data" in result

    def test_log_empty_logs(self, mock_forgejo_client) -> None:  # type: ignore[no-untyped-def]
        mock_forgejo_client.post_web.return_value = {"logs": {}}
        result = actions.log(run_id=38, owner="o", repo="r")
        assert "No log data" in result

    def test_log_infers_context(self, mock_forgejo_client) -> None:  # type: ignore[no-untyped-def]
        mock_forgejo_client.post_web.return_value = {
            "logs": {
                "0": {"lines": [{"message": "hello"}]},
            },
        }
        with patch("forge.services.actions.get_repo_context", return_value=("o", "r")):
            result = actions.log(run_id=1)
            assert "hello" in result

    def test_log_all_steps(self, mock_forgejo_client) -> None:  # type: ignore[no-untyped-def]
        """When step data for requested step is missing, return all available logs."""
        mock_forgejo_client.post_web.return_value = {
            "logs": {
                "0": {"lines": [{"message": "line from step 0"}]},
                "1": {"lines": [{"message": "line from step 1"}]},
            },
        }
        result = actions.log(run_id=38, job=0, step=5, owner="o", repo="r")
        assert "line from step 0" in result
        assert "line from step 1" in result

    def test_log_list_format(self, mock_forgejo_client) -> None:  # type: ignore[no-untyped-def]
        """Handle logs where step data is a plain list."""
        mock_forgejo_client.post_web.return_value = {
            "logs": {
                "0": [
                    {"message": "line one"},
                    {"message": "line two"},
                ],
            },
        }
        result = actions.log(run_id=38, job=0, step=0, owner="o", repo="r")
        assert "line one" in result
        assert "line two" in result

    def test_log_state_fallback(self, mock_forgejo_client) -> None:  # type: ignore[no-untyped-def]
        """When logs key is absent but state.steps exists, format run state."""
        mock_forgejo_client.post_web.return_value = {
            "state": {
                "steps": [
                    {"name": "Checkout", "status": "success"},
                    {"name": "Build", "status": "failure"},
                ],
            },
        }
        result = actions.log(run_id=38, owner="o", repo="r")
        assert "Checkout" in result
        assert "Build" in result


class TestCommitStatus:
    """Tests for commit_status."""

    def test_commit_status(self, mock_forgejo_client) -> None:  # type: ignore[no-untyped-def]
        mock_forgejo_client.get.return_value = [
            {
                "context": "ci/build",
                "status": "success",
                "description": "Build passed",
                "target_url": "https://example.com/build/1",
            },
        ]
        result = actions.commit_status(ref="main", owner="o", repo="r")
        assert "ci/build" in result
        assert "success" in result

    def test_commit_status_empty(self, mock_forgejo_client) -> None:  # type: ignore[no-untyped-def]
        mock_forgejo_client.get.return_value = []
        result = actions.commit_status(ref="main", owner="o", repo="r")
        assert "No statuses found" in result

    def test_commit_status_no_ref(self) -> None:
        result = actions.commit_status(owner="o", repo="r")
        assert "Error" in result

    def test_commit_status_infers_context(self, mock_forgejo_client) -> None:  # type: ignore[no-untyped-def]
        mock_forgejo_client.get.return_value = []
        with patch("forge.services.actions.get_repo_context", return_value=("o", "r")):
            result = actions.commit_status(ref="main")
            assert "No statuses found" in result
