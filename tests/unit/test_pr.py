"""Tests for the PR service."""

from __future__ import annotations

from unittest.mock import patch

from forge.services.pr import PullRequestService


class TestPullRequestService:
    """Tests for PullRequestService."""

    def test_list(self, mock_forgejo_client) -> None:  # type: ignore[no-untyped-def]
        mock_forgejo_client.get.return_value = [
            {
                "number": 1,
                "title": "Feature PR",
                "state": "open",
                "user": {"login": "dev"},
            },
        ]
        svc = PullRequestService(_auto_register=False)
        result = svc.list(owner="o", repo="r")
        assert "Feature PR" in result

    def test_list_empty(self, mock_forgejo_client) -> None:  # type: ignore[no-untyped-def]
        mock_forgejo_client.get.return_value = []
        svc = PullRequestService(_auto_register=False)
        result = svc.list(owner="o", repo="r")
        assert "No pull requests found" in result

    def test_view(self, mock_forgejo_client) -> None:  # type: ignore[no-untyped-def]
        mock_forgejo_client.get.return_value = {
            "number": 10,
            "title": "My PR",
            "state": "open",
            "user": {"login": "dev"},
            "head": {"label": "dev:feature"},
            "base": {"label": "dev:main"},
            "mergeable": True,
            "created_at": "2026-01-01",
            "body": "PR body",
        }
        svc = PullRequestService(_auto_register=False)
        result = svc.view(number=10, owner="o", repo="r")
        assert "#10" in result
        assert "My PR" in result

    def test_view_no_number(self) -> None:
        svc = PullRequestService(_auto_register=False)
        result = svc.view(owner="o", repo="r")
        assert "Error" in result

    def test_create(self, mock_forgejo_client) -> None:  # type: ignore[no-untyped-def]
        mock_forgejo_client.post.return_value = {
            "number": 5,
            "title": "New PR",
            "html_url": "https://example.com/o/r/pulls/5",
        }
        svc = PullRequestService(_auto_register=False)
        result = svc.create(title="New PR", head="feature", owner="o", repo="r")
        assert "#5" in result

    def test_create_no_title(self) -> None:
        svc = PullRequestService(_auto_register=False)
        result = svc.create(head="feature", owner="o", repo="r")
        assert "Error" in result

    def test_create_no_head(self) -> None:
        svc = PullRequestService(_auto_register=False)
        result = svc.create(title="PR", owner="o", repo="r")
        assert "Error" in result

    def test_merge(self, mock_forgejo_client) -> None:  # type: ignore[no-untyped-def]
        mock_forgejo_client.post.return_value = None
        svc = PullRequestService(_auto_register=False)
        result = svc.merge(number=10, method="squash", owner="o", repo="r")
        assert "Merged" in result
        assert "squash" in result

    def test_close(self, mock_forgejo_client) -> None:  # type: ignore[no-untyped-def]
        mock_forgejo_client.patch.return_value = {"number": 10, "state": "closed"}
        svc = PullRequestService(_auto_register=False)
        result = svc.close(number=10, owner="o", repo="r")
        assert "Closed" in result

    def test_reopen(self, mock_forgejo_client) -> None:  # type: ignore[no-untyped-def]
        mock_forgejo_client.patch.return_value = {"number": 10, "state": "open"}
        svc = PullRequestService(_auto_register=False)
        result = svc.reopen(number=10, owner="o", repo="r")
        assert "Reopened" in result

    def test_diff(self, mock_forgejo_client) -> None:  # type: ignore[no-untyped-def]
        mock_forgejo_client.get_raw.return_value = "diff --git a/file.py b/file.py\n+new line"
        svc = PullRequestService(_auto_register=False)
        result = svc.diff(number=10, owner="o", repo="r")
        assert "diff --git" in result

    def test_review(self, mock_forgejo_client) -> None:  # type: ignore[no-untyped-def]
        mock_forgejo_client.post.return_value = {"id": 1}
        svc = PullRequestService(_auto_register=False)
        result = svc.review(number=10, body="LGTM", event="APPROVE", owner="o", repo="r")
        assert "APPROVE" in result

    def test_list_infers_context(self, mock_forgejo_client) -> None:  # type: ignore[no-untyped-def]
        mock_forgejo_client.get.return_value = []
        with patch("forge.services.pr.get_repo_context", return_value=("o", "r")):
            svc = PullRequestService(_auto_register=False)
            result = svc.list()
            assert "No pull requests found" in result

    def test_view_infers_context(self, mock_forgejo_client) -> None:  # type: ignore[no-untyped-def]
        mock_forgejo_client.get.return_value = {
            "number": 1,
            "title": "PR",
            "state": "open",
            "user": {"login": "u"},
            "head": {"label": "u:f"},
            "base": {"label": "u:m"},
            "mergeable": True,
            "created_at": "2026-01-01",
            "body": "",
        }
        with patch("forge.services.pr.get_repo_context", return_value=("o", "r")):
            svc = PullRequestService(_auto_register=False)
            result = svc.view(number=1)
            assert "#1" in result

    def test_create_infers_context(self, mock_forgejo_client) -> None:  # type: ignore[no-untyped-def]
        mock_forgejo_client.post.return_value = {"number": 1, "title": "PR", "html_url": ""}
        with patch("forge.services.pr.get_repo_context", return_value=("o", "r")):
            svc = PullRequestService(_auto_register=False)
            result = svc.create(title="PR", head="feature")
            assert "#1" in result

    def test_create_with_body(self, mock_forgejo_client) -> None:  # type: ignore[no-untyped-def]
        mock_forgejo_client.post.return_value = {"number": 1, "title": "PR", "html_url": ""}
        svc = PullRequestService(_auto_register=False)
        result = svc.create(title="PR", head="f", body="Description", owner="o", repo="r")
        assert "#1" in result
        call_json = mock_forgejo_client.post.call_args[1]["json"]
        assert call_json["body"] == "Description"

    def test_merge_infers_context(self, mock_forgejo_client) -> None:  # type: ignore[no-untyped-def]
        mock_forgejo_client.post.return_value = None
        with patch("forge.services.pr.get_repo_context", return_value=("o", "r")):
            svc = PullRequestService(_auto_register=False)
            result = svc.merge(number=1)
            assert "Merged" in result

    def test_merge_no_number(self) -> None:
        svc = PullRequestService(_auto_register=False)
        result = svc.merge(owner="o", repo="r")
        assert "Error" in result

    def test_close_infers_context(self, mock_forgejo_client) -> None:  # type: ignore[no-untyped-def]
        mock_forgejo_client.patch.return_value = {"number": 1, "state": "closed"}
        with patch("forge.services.pr.get_repo_context", return_value=("o", "r")):
            svc = PullRequestService(_auto_register=False)
            result = svc.close(number=1)
            assert "Closed" in result

    def test_close_no_number(self) -> None:
        svc = PullRequestService(_auto_register=False)
        result = svc.close(owner="o", repo="r")
        assert "Error" in result

    def test_reopen_infers_context(self, mock_forgejo_client) -> None:  # type: ignore[no-untyped-def]
        mock_forgejo_client.patch.return_value = {"number": 1, "state": "open"}
        with patch("forge.services.pr.get_repo_context", return_value=("o", "r")):
            svc = PullRequestService(_auto_register=False)
            result = svc.reopen(number=1)
            assert "Reopened" in result

    def test_reopen_no_number(self) -> None:
        svc = PullRequestService(_auto_register=False)
        result = svc.reopen(owner="o", repo="r")
        assert "Error" in result

    def test_diff_infers_context(self, mock_forgejo_client) -> None:  # type: ignore[no-untyped-def]
        mock_forgejo_client.get_raw.return_value = "diff text"
        with patch("forge.services.pr.get_repo_context", return_value=("o", "r")):
            svc = PullRequestService(_auto_register=False)
            result = svc.diff(number=1)
            assert "diff text" in result

    def test_diff_no_number(self) -> None:
        svc = PullRequestService(_auto_register=False)
        result = svc.diff(owner="o", repo="r")
        assert "Error" in result

    def test_review_infers_context(self, mock_forgejo_client) -> None:  # type: ignore[no-untyped-def]
        mock_forgejo_client.post.return_value = {"id": 1}
        with patch("forge.services.pr.get_repo_context", return_value=("o", "r")):
            svc = PullRequestService(_auto_register=False)
            result = svc.review(number=1, event="APPROVE")
            assert "APPROVE" in result

    def test_review_no_number(self) -> None:
        svc = PullRequestService(_auto_register=False)
        result = svc.review(owner="o", repo="r")
        assert "Error" in result

    def test_review_with_body(self, mock_forgejo_client) -> None:  # type: ignore[no-untyped-def]
        mock_forgejo_client.post.return_value = {"id": 1}
        svc = PullRequestService(_auto_register=False)
        result = svc.review(number=1, body="LGTM", event="COMMENT", owner="o", repo="r")
        assert "COMMENT" in result
