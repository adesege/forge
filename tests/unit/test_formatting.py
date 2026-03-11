"""Tests for Forgejo output formatting."""

from __future__ import annotations

from forge.forgejo.formatting import (
    format_issue,
    format_json,
    format_org,
    format_pr,
    format_release,
    format_repo,
    format_table,
    format_user,
)


class TestFormatTable:
    """Tests for format_table."""

    def test_basic_table(self) -> None:
        rows = [{"name": "repo1", "stars": 5}, {"name": "repo2", "stars": 10}]
        result = format_table(rows, [("name", "Name"), ("stars", "Stars")])
        assert "repo1" in result
        assert "repo2" in result
        assert "Name" in result
        assert "Stars" in result

    def test_empty_rows(self) -> None:
        result = format_table([], [("name", "Name")])
        assert "Name" in result  # Header still shown

    def test_with_title(self) -> None:
        result = format_table([{"a": "b"}], [("a", "A")], title="My Table")
        # Title may be word-wrapped or have ANSI codes; check both words present
        assert "My" in result
        assert "Table" in result


class TestFormatRepo:
    """Tests for format_repo."""

    def test_basic_repo(self) -> None:
        repo = {
            "full_name": "owner/repo",
            "description": "A test repo",
            "private": False,
            "stars_count": 42,
            "forks_count": 5,
            "language": "Python",
            "default_branch": "main",
            "html_url": "https://git.example.com/owner/repo",
        }
        result = format_repo(repo)
        assert "owner/repo" in result
        assert "public" in result
        assert "42" in result
        assert "Python" in result

    def test_private_repo(self) -> None:
        result = format_repo({"full_name": "x/y", "private": True})
        assert "private" in result


class TestFormatIssue:
    """Tests for format_issue."""

    def test_basic_issue(self) -> None:
        issue = {
            "number": 42,
            "title": "Bug report",
            "state": "open",
            "user": {"login": "alice"},
            "labels": [{"name": "bug"}],
            "assignees": [{"login": "bob"}],
            "created_at": "2026-01-01T00:00:00Z",
            "body": "Something is broken",
        }
        result = format_issue(issue)
        assert "#42" in result
        assert "Bug report" in result
        assert "open" in result
        assert "alice" in result
        assert "bug" in result
        assert "bob" in result


class TestFormatPr:
    """Tests for format_pr."""

    def test_basic_pr(self) -> None:
        pr = {
            "number": 10,
            "title": "Add feature",
            "state": "open",
            "user": {"login": "dev"},
            "head": {"label": "dev:feature"},
            "base": {"label": "dev:main"},
            "mergeable": True,
            "created_at": "2026-01-01T00:00:00Z",
            "body": "New feature",
        }
        result = format_pr(pr)
        assert "#10" in result
        assert "Add feature" in result
        assert "dev" in result


class TestFormatRelease:
    """Tests for format_release."""

    def test_basic_release(self) -> None:
        release = {
            "tag_name": "v1.0.0",
            "name": "Version 1.0.0",
            "author": {"login": "maintainer"},
            "published_at": "2026-01-01T00:00:00Z",
            "body": "Release notes here",
            "draft": False,
            "prerelease": False,
            "assets": [{"name": "app.tar.gz", "size": 1024}],
        }
        result = format_release(release)
        assert "v1.0.0" in result
        assert "Version 1.0.0" in result
        assert "app.tar.gz" in result


class TestFormatUser:
    """Tests for format_user."""

    def test_basic_user(self) -> None:
        user = {
            "login": "testuser",
            "full_name": "Test User",
            "email": "test@example.com",
            "is_admin": False,
        }
        result = format_user(user)
        assert "testuser" in result
        assert "Test User" in result
        assert "test@example.com" in result


class TestFormatOrg:
    """Tests for format_org."""

    def test_basic_org(self) -> None:
        org = {
            "username": "myorg",
            "description": "My organization",
            "visibility": "public",
            "location": "Earth",
            "website": "https://example.com",
        }
        result = format_org(org)
        assert "myorg" in result
        assert "My organization" in result


class TestFormatJson:
    """Tests for format_json."""

    def test_formats_dict(self) -> None:
        result = format_json({"key": "value"})
        assert '"key": "value"' in result
