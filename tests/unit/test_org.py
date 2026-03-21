"""Tests for the org service."""

from __future__ import annotations

from forge.services import org


class TestOrgService:
    """Tests for org service functions."""

    def test_list(self, mock_forgejo_client) -> None:  # type: ignore[no-untyped-def]
        mock_forgejo_client.get.return_value = [
            {
                "username": "myorg",
                "description": "My org",
                "visibility": "public",
            },
        ]
        result = org.list_orgs()
        assert "myorg" in result

    def test_list_empty(self, mock_forgejo_client) -> None:  # type: ignore[no-untyped-def]
        mock_forgejo_client.get.return_value = []
        result = org.list_orgs()
        assert "No organizations found" in result

    def test_view(self, mock_forgejo_client) -> None:  # type: ignore[no-untyped-def]
        mock_forgejo_client.get.return_value = {
            "username": "myorg",
            "description": "My org",
            "visibility": "public",
            "location": "Earth",
            "website": "https://example.com",
        }
        result = org.view(org="myorg")
        assert "myorg" in result

    def test_view_no_org(self) -> None:
        result = org.view()
        assert "Error" in result

    def test_repos(self, mock_forgejo_client) -> None:  # type: ignore[no-untyped-def]
        mock_forgejo_client.get.return_value = [
            {
                "full_name": "myorg/repo1",
                "description": "",
                "stars_count": 0,
                "language": "Python",
            },
        ]
        result = org.repos(org="myorg")
        assert "myorg/repo1" in result

    def test_repos_no_org(self) -> None:
        result = org.repos()
        assert "Error" in result

    def test_members(self, mock_forgejo_client) -> None:  # type: ignore[no-untyped-def]
        mock_forgejo_client.get.return_value = [
            {"login": "alice", "full_name": "Alice", "email": "alice@example.com"},
        ]
        result = org.members(org="myorg")
        assert "alice" in result

    def test_members_no_org(self) -> None:
        result = org.members()
        assert "Error" in result
