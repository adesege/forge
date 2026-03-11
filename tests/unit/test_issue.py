"""Tests for the issue service."""

from __future__ import annotations

from unittest.mock import patch

from forge.services.issue import IssueService


class TestIssueService:
    """Tests for IssueService."""

    def test_list(self, mock_forgejo_client) -> None:  # type: ignore[no-untyped-def]
        mock_forgejo_client.get.return_value = [
            {
                "number": 1,
                "title": "Bug",
                "state": "open",
                "user": {"login": "alice"},
            },
        ]
        svc = IssueService(_auto_register=False)
        result = svc.list(owner="o", repo="r")
        assert "Bug" in result

    def test_list_infers_context(self, mock_forgejo_client) -> None:  # type: ignore[no-untyped-def]
        mock_forgejo_client.get.return_value = []
        with patch("forge.services.issue.get_repo_context", return_value=("o", "r")):
            svc = IssueService(_auto_register=False)
            result = svc.list()
            assert "No issues found" in result

    def test_list_empty(self, mock_forgejo_client) -> None:  # type: ignore[no-untyped-def]
        mock_forgejo_client.get.return_value = []
        svc = IssueService(_auto_register=False)
        result = svc.list(owner="o", repo="r")
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
        svc = IssueService(_auto_register=False)
        result = svc.view(number=42, owner="o", repo="r")
        assert "#42" in result
        assert "Test issue" in result

    def test_view_no_number(self) -> None:
        svc = IssueService(_auto_register=False)
        result = svc.view(owner="o", repo="r")
        assert "Error" in result

    def test_create(self, mock_forgejo_client) -> None:  # type: ignore[no-untyped-def]
        mock_forgejo_client.post.return_value = {
            "number": 5,
            "title": "New issue",
            "html_url": "https://example.com/o/r/issues/5",
        }
        svc = IssueService(_auto_register=False)
        result = svc.create(title="New issue", owner="o", repo="r")
        assert "#5" in result

    def test_create_no_title(self) -> None:
        svc = IssueService(_auto_register=False)
        result = svc.create(owner="o", repo="r")
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
        svc = IssueService(_auto_register=False)
        result = svc.create(title="Labeled", labels="bug,enhancement", owner="o", repo="r")
        assert "#6" in result
        call_args = mock_forgejo_client.post.call_args
        assert call_args[1]["json"]["labels"] == [1, 2]

    def test_close(self, mock_forgejo_client) -> None:  # type: ignore[no-untyped-def]
        mock_forgejo_client.patch.return_value = {"number": 1, "state": "closed"}
        svc = IssueService(_auto_register=False)
        result = svc.close(number=1, owner="o", repo="r")
        assert "Closed" in result

    def test_reopen(self, mock_forgejo_client) -> None:  # type: ignore[no-untyped-def]
        mock_forgejo_client.patch.return_value = {"number": 1, "state": "open"}
        svc = IssueService(_auto_register=False)
        result = svc.reopen(number=1, owner="o", repo="r")
        assert "Reopened" in result

    def test_comment(self, mock_forgejo_client) -> None:  # type: ignore[no-untyped-def]
        mock_forgejo_client.post.return_value = {"html_url": "https://example.com/comment/1"}
        svc = IssueService(_auto_register=False)
        result = svc.comment(number=1, body="Fixed", owner="o", repo="r")
        assert "Added comment" in result

    def test_comment_no_body(self) -> None:
        svc = IssueService(_auto_register=False)
        result = svc.comment(number=1, owner="o", repo="r")
        assert "Error" in result

    def test_edit(self, mock_forgejo_client) -> None:  # type: ignore[no-untyped-def]
        mock_forgejo_client.patch.return_value = {"number": 1, "title": "Updated"}
        svc = IssueService(_auto_register=False)
        result = svc.edit(number=1, title="Updated", owner="o", repo="r")
        assert "Updated" in result

    def test_edit_nothing(self) -> None:
        svc = IssueService(_auto_register=False)
        result = svc.edit(number=1, owner="o", repo="r")
        assert "Error" in result
