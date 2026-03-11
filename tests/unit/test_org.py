"""Tests for the org service."""

from __future__ import annotations

from forge.services.org import OrgService


class TestOrgService:
    """Tests for OrgService."""

    def test_list(self, mock_forgejo_client) -> None:  # type: ignore[no-untyped-def]
        mock_forgejo_client.get.return_value = [
            {
                "username": "myorg",
                "description": "My org",
                "visibility": "public",
            },
        ]
        svc = OrgService(_auto_register=False)
        result = svc.list()
        assert "myorg" in result

    def test_list_empty(self, mock_forgejo_client) -> None:  # type: ignore[no-untyped-def]
        mock_forgejo_client.get.return_value = []
        svc = OrgService(_auto_register=False)
        result = svc.list()
        assert "No organizations found" in result

    def test_view(self, mock_forgejo_client) -> None:  # type: ignore[no-untyped-def]
        mock_forgejo_client.get.return_value = {
            "username": "myorg",
            "description": "My org",
            "visibility": "public",
            "location": "Earth",
            "website": "https://example.com",
        }
        svc = OrgService(_auto_register=False)
        result = svc.view(org="myorg")
        assert "myorg" in result

    def test_view_no_org(self) -> None:
        svc = OrgService(_auto_register=False)
        result = svc.view()
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
        svc = OrgService(_auto_register=False)
        result = svc.repos(org="myorg")
        assert "myorg/repo1" in result

    def test_repos_no_org(self) -> None:
        svc = OrgService(_auto_register=False)
        result = svc.repos()
        assert "Error" in result

    def test_members(self, mock_forgejo_client) -> None:  # type: ignore[no-untyped-def]
        mock_forgejo_client.get.return_value = [
            {"login": "alice", "full_name": "Alice", "email": "alice@example.com"},
        ]
        svc = OrgService(_auto_register=False)
        result = svc.members(org="myorg")
        assert "alice" in result

    def test_members_no_org(self) -> None:
        svc = OrgService(_auto_register=False)
        result = svc.members()
        assert "Error" in result
