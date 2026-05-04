"""Tests for the PR service."""

from __future__ import annotations

import json
from unittest.mock import patch

from forge.services import pr


class TestPullRequestService:
    """Tests for PR service functions."""

    def test_list(self, mock_forgejo_client) -> None:  # type: ignore[no-untyped-def]
        mock_forgejo_client.get.return_value = [
            {
                "number": 1,
                "title": "Feature PR",
                "state": "open",
                "user": {"login": "dev"},
            },
        ]
        result = pr.list_prs(owner="o", repo="r")
        assert "Feature PR" in result

    def test_list_empty(self, mock_forgejo_client) -> None:  # type: ignore[no-untyped-def]
        mock_forgejo_client.get.return_value = []
        result = pr.list_prs(owner="o", repo="r")
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
        result = pr.view(number=10, owner="o", repo="r")
        assert "#10" in result
        assert "My PR" in result

    def test_view_no_number(self) -> None:
        result = pr.view(owner="o", repo="r")
        assert "Error" in result

    def test_create(self, mock_forgejo_client) -> None:  # type: ignore[no-untyped-def]
        mock_forgejo_client.post.return_value = {
            "number": 5,
            "title": "New PR",
            "html_url": "https://example.com/o/r/pulls/5",
        }
        result = pr.create(title="New PR", head="feature", owner="o", repo="r")
        assert "#5" in result

    def test_create_no_title(self) -> None:
        result = pr.create(head="feature", owner="o", repo="r")
        assert "Error" in result

    def test_create_no_head(self) -> None:
        result = pr.create(title="PR", owner="o", repo="r")
        assert "Error" in result

    def test_merge(self, mock_forgejo_client) -> None:  # type: ignore[no-untyped-def]
        mock_forgejo_client.post.return_value = None
        result = pr.merge(number=10, method="squash", owner="o", repo="r")
        assert "Merged" in result
        assert "squash" in result

    def test_close(self, mock_forgejo_client) -> None:  # type: ignore[no-untyped-def]
        mock_forgejo_client.patch.return_value = {"number": 10, "state": "closed"}
        result = pr.close(number=10, owner="o", repo="r")
        assert "Closed" in result

    def test_reopen(self, mock_forgejo_client) -> None:  # type: ignore[no-untyped-def]
        mock_forgejo_client.patch.return_value = {"number": 10, "state": "open"}
        result = pr.reopen(number=10, owner="o", repo="r")
        assert "Reopened" in result

    def test_diff(self, mock_forgejo_client) -> None:  # type: ignore[no-untyped-def]
        mock_forgejo_client.get_raw.return_value = "diff --git a/file.py b/file.py\n+new line"
        result = pr.diff(number=10, owner="o", repo="r")
        assert "diff --git" in result

    def test_review(self, mock_forgejo_client) -> None:  # type: ignore[no-untyped-def]
        mock_forgejo_client.post.return_value = {"id": 1}
        result = pr.review(number=10, body="LGTM", event="APPROVE", owner="o", repo="r")
        assert "APPROVE" in result

    def test_list_owner_only(self, mock_forgejo_client) -> None:  # type: ignore[no-untyped-def]
        mock_forgejo_client.get.side_effect = [
            [{"name": "repo-a"}, {"name": "repo-b"}],  # repos list
            [
                {
                    "number": 1,
                    "title": "PR in A",
                    "state": "open",
                    "user": {"login": "dev"},
                    "updated_at": "2026-01-02",
                }
            ],
            [
                {
                    "number": 2,
                    "title": "PR in B",
                    "state": "open",
                    "user": {"login": "dev"},
                    "updated_at": "2026-01-01",
                }
            ],
        ]
        result = pr.list_prs(owner="myorg")
        assert "PR in A" in result
        assert "PR in B" in result
        assert "repo-a" in result
        assert "repo-b" in result

    def test_list_owner_only_skips_404_repos(self, mock_forgejo_client) -> None:  # type: ignore[no-untyped-def]
        from forge.forgejo.exceptions import ForgejoNotFoundError

        mock_forgejo_client.get.side_effect = [
            [{"name": "repo-a"}, {"name": "repo-b"}],  # repos list
            ForgejoNotFoundError("not found"),  # repo-a returns 404
            [
                {
                    "number": 2,
                    "title": "PR in B",
                    "state": "open",
                    "user": {"login": "dev"},
                    "updated_at": "2026-01-01",
                }
            ],
        ]
        result = pr.list_prs(owner="myorg")
        assert "PR in B" in result

    def test_list_owner_only_no_repos(self, mock_forgejo_client) -> None:  # type: ignore[no-untyped-def]
        mock_forgejo_client.get.return_value = []
        result = pr.list_prs(owner="myorg")
        assert "No repositories found" in result

    def test_list_owner_only_no_prs(self, mock_forgejo_client) -> None:  # type: ignore[no-untyped-def]
        mock_forgejo_client.get.side_effect = [
            [{"name": "repo-a"}],  # repos list
            [],  # no PRs in repo-a
        ]
        result = pr.list_prs(owner="myorg")
        assert "No pull requests found" in result

    def test_list_uses_default_owner(self, mock_forgejo_client) -> None:  # type: ignore[no-untyped-def]
        mock_forgejo_client.get.side_effect = [
            [{"name": "repo-a"}],
            [
                {
                    "number": 1,
                    "title": "Default owner PR",
                    "state": "open",
                    "user": {"login": "dev"},
                    "updated_at": "2026-01-01",
                }
            ],
        ]
        with patch("forge.services.pr.get_default_owner", return_value="default-org"):
            result = pr.list_prs()
            assert "Default owner PR" in result

    def test_list_infers_context(self, mock_forgejo_client) -> None:  # type: ignore[no-untyped-def]
        mock_forgejo_client.get.return_value = []
        with (
            patch("forge.services.pr.get_default_owner", return_value=""),
            patch("forge.services.pr.get_repo_context", return_value=("o", "r")),
        ):
            result = pr.list_prs()
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
            result = pr.view(number=1)
            assert "#1" in result

    def test_create_infers_context(self, mock_forgejo_client) -> None:  # type: ignore[no-untyped-def]
        mock_forgejo_client.post.return_value = {"number": 1, "title": "PR", "html_url": ""}
        with patch("forge.services.pr.get_repo_context", return_value=("o", "r")):
            result = pr.create(title="PR", head="feature")
            assert "#1" in result

    def test_create_with_body(self, mock_forgejo_client) -> None:  # type: ignore[no-untyped-def]
        mock_forgejo_client.post.return_value = {"number": 1, "title": "PR", "html_url": ""}
        result = pr.create(title="PR", head="f", body="Description", owner="o", repo="r")
        assert "#1" in result
        call_json = mock_forgejo_client.post.call_args[1]["json"]
        assert call_json["body"] == "Description"

    def test_merge_infers_context(self, mock_forgejo_client) -> None:  # type: ignore[no-untyped-def]
        mock_forgejo_client.post.return_value = None
        with patch("forge.services.pr.get_repo_context", return_value=("o", "r")):
            result = pr.merge(number=1)
            assert "Merged" in result

    def test_merge_no_number(self) -> None:
        result = pr.merge(owner="o", repo="r")
        assert "Error" in result

    def test_close_infers_context(self, mock_forgejo_client) -> None:  # type: ignore[no-untyped-def]
        mock_forgejo_client.patch.return_value = {"number": 1, "state": "closed"}
        with patch("forge.services.pr.get_repo_context", return_value=("o", "r")):
            result = pr.close(number=1)
            assert "Closed" in result

    def test_close_no_number(self) -> None:
        result = pr.close(owner="o", repo="r")
        assert "Error" in result

    def test_reopen_infers_context(self, mock_forgejo_client) -> None:  # type: ignore[no-untyped-def]
        mock_forgejo_client.patch.return_value = {"number": 1, "state": "open"}
        with patch("forge.services.pr.get_repo_context", return_value=("o", "r")):
            result = pr.reopen(number=1)
            assert "Reopened" in result

    def test_reopen_no_number(self) -> None:
        result = pr.reopen(owner="o", repo="r")
        assert "Error" in result

    def test_diff_infers_context(self, mock_forgejo_client) -> None:  # type: ignore[no-untyped-def]
        mock_forgejo_client.get_raw.return_value = "diff text"
        with patch("forge.services.pr.get_repo_context", return_value=("o", "r")):
            result = pr.diff(number=1)
            assert "diff text" in result

    def test_diff_no_number(self) -> None:
        result = pr.diff(owner="o", repo="r")
        assert "Error" in result

    def test_review_infers_context(self, mock_forgejo_client) -> None:  # type: ignore[no-untyped-def]
        mock_forgejo_client.post.return_value = {"id": 1}
        with patch("forge.services.pr.get_repo_context", return_value=("o", "r")):
            result = pr.review(number=1, event="APPROVE")
            assert "APPROVE" in result

    def test_review_no_number(self) -> None:
        result = pr.review(owner="o", repo="r")
        assert "Error" in result

    def test_review_with_body(self, mock_forgejo_client) -> None:  # type: ignore[no-untyped-def]
        mock_forgejo_client.post.return_value = {"id": 1}
        result = pr.review(number=1, body="LGTM", event="COMMENT", owner="o", repo="r")
        assert "COMMENT" in result

    def test_checks_no_number(self) -> None:
        result = pr.checks(owner="o", repo="r")
        assert "Error" in result

    def test_checks_no_head_sha(self, mock_forgejo_client) -> None:  # type: ignore[no-untyped-def]
        mock_forgejo_client.get.return_value = {
            "head": {"sha": ""},
        }
        result = pr.checks(number=1, owner="o", repo="r")
        assert "no head commit SHA" in result

    def test_checks_no_statuses(self, mock_forgejo_client) -> None:  # type: ignore[no-untyped-def]
        mock_forgejo_client.get.side_effect = [
            {"head": {"sha": "abc123def456"}},  # PR data
            [],  # statuses
            {"workflow_runs": []},  # action runs
        ]
        result = pr.checks(number=1, owner="o", repo="r")
        assert "PR #1" in result
        assert "No checks found" in result

    def test_checks_with_statuses(self, mock_forgejo_client) -> None:  # type: ignore[no-untyped-def]
        mock_forgejo_client.get.side_effect = [
            {"head": {"sha": "abc123def456"}},  # PR data
            [
                {
                    "context": "CI / lint-and-test",
                    "status": "success",
                    "description": "All checks passed",
                    "target_url": "",
                },
            ],
            {"workflow_runs": []},  # action runs
        ]
        result = pr.checks(number=5, owner="o", repo="r")
        assert "PR #5" in result
        assert "abc123def456"[:12] in result
        assert "CI / lint-and-test" in result
        assert "success" in result

    def test_checks_with_steps(self, mock_forgejo_client) -> None:  # type: ignore[no-untyped-def]
        step_data = {
            "state": {
                "run": {
                    "steps": [
                        {
                            "name": "Lint",
                            "status": "failure",
                            "duration": "5s",
                            "logLines": [{"message": "error: clippy failed"}],
                        }
                    ]
                }
            }
        }
        raw = json.dumps(step_data)
        html = f'<div data-initial-post-response="{raw.replace(chr(34), "&quot;")}"></div>'
        mock_forgejo_client.get.side_effect = [
            {"head": {"sha": "abc123def456"}},
            [
                {
                    "context": "CI",
                    "status": "failure",
                    "description": "",
                    "target_url": "https://host/o/r/actions/runs/42",
                },
            ],
            {"workflow_runs": []},
        ]
        mock_forgejo_client.get_html.return_value = html
        result = pr.checks(number=1, owner="o", repo="r")
        assert "CI" in result

    def test_checks_infers_context(self, mock_forgejo_client) -> None:  # type: ignore[no-untyped-def]
        mock_forgejo_client.get.side_effect = [
            {"head": {"sha": "abc123def456"}},
            [],
            {"workflow_runs": []},
        ]
        with patch("forge.services.pr.get_repo_context", return_value=("o", "r")):
            result = pr.checks(number=1)
            assert "No checks found" in result

    def test_scrape_steps_empty_html(self) -> None:
        from forge.services.pr import _scrape_steps

        assert _scrape_steps("") == []
        assert _scrape_steps("<div>no data</div>") == []

    def test_scrape_steps_valid(self) -> None:
        import json

        from forge.services.pr import _scrape_steps

        data = {
            "state": {
                "run": {
                    "steps": [
                        {"name": "Build", "status": "success", "duration": "10s"},
                        {
                            "name": "Test",
                            "status": "failure",
                            "duration": "3s",
                            "logLines": [{"message": "FAIL test_foo"}],
                        },
                    ]
                }
            }
        }
        raw_json = json.dumps(data)
        html = f'<div data-initial-post-response="{raw_json.replace(chr(34), "&quot;")}"></div>'
        steps = _scrape_steps(html)
        assert len(steps) == 2
        assert steps[0]["name"] == "Build"
        assert steps[0]["status"] == "success"
        assert steps[1]["name"] == "Test"
        assert "FAIL test_foo" in steps[1]["log"]
