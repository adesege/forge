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

    def test_view_infers_context(self, mock_forgejo_client) -> None:  # type: ignore[no-untyped-def]
        mock_forgejo_client.get.return_value = {
            "number": 1,
            "title": "Test",
            "state": "open",
            "user": {"login": "u"},
            "labels": [],
            "assignees": [],
            "created_at": "2026-01-01",
            "body": "",
        }
        with patch("forge.services.issue.get_repo_context", return_value=("o", "r")):
            svc = IssueService(_auto_register=False)
            result = svc.view(number=1)
            assert "#1" in result

    def test_create_infers_context(self, mock_forgejo_client) -> None:  # type: ignore[no-untyped-def]
        mock_forgejo_client.post.return_value = {"number": 1, "title": "T", "html_url": ""}
        with patch("forge.services.issue.get_repo_context", return_value=("o", "r")):
            svc = IssueService(_auto_register=False)
            result = svc.create(title="T")
            assert "#1" in result

    def test_create_with_body_and_assignees_and_milestone(self, mock_forgejo_client) -> None:  # type: ignore[no-untyped-def]
        mock_forgejo_client.post.return_value = {"number": 7, "title": "Full", "html_url": ""}
        svc = IssueService(_auto_register=False)
        result = svc.create(
            title="Full",
            body="body text",
            assignees="alice,bob",
            milestone=3,
            owner="o",
            repo="r",
        )
        assert "#7" in result
        call_json = mock_forgejo_client.post.call_args[1]["json"]
        assert call_json["body"] == "body text"
        assert call_json["assignees"] == ["alice", "bob"]
        assert call_json["milestone"] == 3

    def test_close_infers_context(self, mock_forgejo_client) -> None:  # type: ignore[no-untyped-def]
        mock_forgejo_client.patch.return_value = {"number": 1, "state": "closed"}
        with patch("forge.services.issue.get_repo_context", return_value=("o", "r")):
            svc = IssueService(_auto_register=False)
            result = svc.close(number=1)
            assert "Closed" in result

    def test_close_no_number(self) -> None:
        svc = IssueService(_auto_register=False)
        result = svc.close(owner="o", repo="r")
        assert "Error" in result

    def test_reopen_infers_context(self, mock_forgejo_client) -> None:  # type: ignore[no-untyped-def]
        mock_forgejo_client.patch.return_value = {"number": 1, "state": "open"}
        with patch("forge.services.issue.get_repo_context", return_value=("o", "r")):
            svc = IssueService(_auto_register=False)
            result = svc.reopen(number=1)
            assert "Reopened" in result

    def test_reopen_no_number(self) -> None:
        svc = IssueService(_auto_register=False)
        result = svc.reopen(owner="o", repo="r")
        assert "Error" in result

    def test_comment_infers_context(self, mock_forgejo_client) -> None:  # type: ignore[no-untyped-def]
        mock_forgejo_client.post.return_value = {"html_url": ""}
        with patch("forge.services.issue.get_repo_context", return_value=("o", "r")):
            svc = IssueService(_auto_register=False)
            result = svc.comment(number=1, body="txt")
            assert "Added comment" in result

    def test_comment_no_number(self) -> None:
        svc = IssueService(_auto_register=False)
        result = svc.comment(body="txt", owner="o", repo="r")
        assert "Error" in result

    def test_edit_infers_context(self, mock_forgejo_client) -> None:  # type: ignore[no-untyped-def]
        mock_forgejo_client.patch.return_value = {"number": 1, "title": "T"}
        with patch("forge.services.issue.get_repo_context", return_value=("o", "r")):
            svc = IssueService(_auto_register=False)
            result = svc.edit(number=1, title="T")
            assert "Updated" in result

    def test_edit_no_number(self) -> None:
        svc = IssueService(_auto_register=False)
        result = svc.edit(owner="o", repo="r")
        assert "Error" in result

    def test_edit_body_only(self, mock_forgejo_client) -> None:  # type: ignore[no-untyped-def]
        mock_forgejo_client.patch.return_value = {"number": 1, "title": "T"}
        svc = IssueService(_auto_register=False)
        result = svc.edit(number=1, body="new body", owner="o", repo="r")
        assert "Updated" in result

    def test_resolve_labels_empty(self, mock_forgejo_client) -> None:  # type: ignore[no-untyped-def]
        svc = IssueService(_auto_register=False)
        result = svc._resolve_labels(mock_forgejo_client, "o", "r", "")
        assert result == []
