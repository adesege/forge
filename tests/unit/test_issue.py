"""Tests for the issue service."""

from __future__ import annotations

from unittest.mock import patch

from forge.services import issue


class TestIssueService:
    """Tests for issue service functions."""

    def test_list(self, mock_forgejo_client) -> None:  # type: ignore[no-untyped-def]
        mock_forgejo_client.get.return_value = [
            {
                "number": 1,
                "title": "Bug",
                "state": "open",
                "user": {"login": "alice"},
            },
        ]
        result = issue.list_issues(owner="o", repo="r")
        assert "Bug" in result

    def test_list_infers_context(self, mock_forgejo_client) -> None:  # type: ignore[no-untyped-def]
        mock_forgejo_client.get.return_value = []
        with patch("forge.services.issue.get_repo_context", return_value=("o", "r")):
            result = issue.list_issues()
            assert "No issues found" in result

    def test_list_empty(self, mock_forgejo_client) -> None:  # type: ignore[no-untyped-def]
        mock_forgejo_client.get.return_value = []
        result = issue.list_issues(owner="o", repo="r")
        assert "No issues found" in result

    def test_view(self, mock_forgejo_client) -> None:  # type: ignore[no-untyped-def]
        mock_forgejo_client.get.return_value = {
            "number": 42,
            "title": "Test issue",
            "state": "open",
            "user": {"login": "bob"},
            "labels": [],
            "assignees": [],
            "created_at": "2026-01-01",
            "body": "Details",
        }
        result = issue.view(number=42, owner="o", repo="r")
        assert "#42" in result
        assert "Test issue" in result

    def test_view_no_number(self) -> None:
        result = issue.view(owner="o", repo="r")
        assert "Error" in result

    def test_create(self, mock_forgejo_client) -> None:  # type: ignore[no-untyped-def]
        mock_forgejo_client.post.return_value = {
            "number": 5,
            "title": "New issue",
            "html_url": "https://example.com/o/r/issues/5",
        }
        result = issue.create(title="New issue", owner="o", repo="r")
        assert "#5" in result

    def test_create_no_title(self) -> None:
        result = issue.create(owner="o", repo="r")
        assert "Error" in result

    def test_create_with_labels(self, mock_forgejo_client) -> None:  # type: ignore[no-untyped-def]
        mock_forgejo_client.get.return_value = [
            {"name": "bug", "id": 1},
            {"name": "enhancement", "id": 2},
        ]
        mock_forgejo_client.post.return_value = {
            "number": 6,
            "title": "Labeled",
            "html_url": "",
        }
        result = issue.create(title="Labeled", labels="bug,enhancement", owner="o", repo="r")
        assert "#6" in result
        call_args = mock_forgejo_client.post.call_args
        assert call_args[1]["json"]["labels"] == [1, 2]

    def test_close(self, mock_forgejo_client) -> None:  # type: ignore[no-untyped-def]
        mock_forgejo_client.patch.return_value = {"number": 1, "state": "closed"}
        result = issue.close(number=1, owner="o", repo="r")
        assert "Closed" in result

    def test_reopen(self, mock_forgejo_client) -> None:  # type: ignore[no-untyped-def]
        mock_forgejo_client.patch.return_value = {"number": 1, "state": "open"}
        result = issue.reopen(number=1, owner="o", repo="r")
        assert "Reopened" in result

    def test_comment(self, mock_forgejo_client) -> None:  # type: ignore[no-untyped-def]
        mock_forgejo_client.post.return_value = {"html_url": "https://example.com/comment/1"}
        result = issue.comment(number=1, body="Fixed", owner="o", repo="r")
        assert "Added comment" in result

    def test_comment_no_body(self) -> None:
        result = issue.comment(number=1, owner="o", repo="r")
        assert "Error" in result

    def test_edit(self, mock_forgejo_client) -> None:  # type: ignore[no-untyped-def]
        mock_forgejo_client.patch.return_value = {"number": 1, "title": "Updated"}
        result = issue.edit(number=1, title="Updated", owner="o", repo="r")
        assert "Updated" in result

    def test_edit_nothing(self) -> None:
        result = issue.edit(number=1, owner="o", repo="r")
        assert "Error" in result
