"""Tests for the release service."""

from __future__ import annotations

from unittest.mock import patch

from forge.services.release import ReleaseService


class TestReleaseService:
    """Tests for ReleaseService."""

    def test_list(self, mock_forgejo_client) -> None:  # type: ignore[no-untyped-def]
        mock_forgejo_client.get.return_value = [
            {
                "tag_name": "v1.0.0",
                "name": "Release 1",
                "author": {"login": "dev"},
                "published_at": "2026-01-01",
            },
        ]
        svc = ReleaseService(_auto_register=False)
        result = svc.list(owner="o", repo="r")
        assert "v1.0.0" in result

    def test_list_empty(self, mock_forgejo_client) -> None:  # type: ignore[no-untyped-def]
        mock_forgejo_client.get.return_value = []
        svc = ReleaseService(_auto_register=False)
        result = svc.list(owner="o", repo="r")
        assert "No releases found" in result

    def test_view(self, mock_forgejo_client) -> None:  # type: ignore[no-untyped-def]
        mock_forgejo_client.get.return_value = {
            "tag_name": "v1.0.0",
            "name": "Version 1",
            "author": {"login": "dev"},
            "published_at": "2026-01-01",
            "body": "Notes",
            "draft": False,
            "prerelease": False,
            "assets": [],
        }
        svc = ReleaseService(_auto_register=False)
        result = svc.view(tag="v1.0.0", owner="o", repo="r")
        assert "Version 1" in result

    def test_view_no_tag(self) -> None:
        svc = ReleaseService(_auto_register=False)
        result = svc.view(owner="o", repo="r")
        assert "Error" in result

    def test_create(self, mock_forgejo_client) -> None:  # type: ignore[no-untyped-def]
        mock_forgejo_client.post.return_value = {
            "name": "v2.0.0",
            "html_url": "https://example.com/releases/v2.0.0",
        }
        svc = ReleaseService(_auto_register=False)
        result = svc.create(tag="v2.0.0", title="Version 2", owner="o", repo="r")
        assert "v2.0.0" in result

    def test_create_no_tag(self) -> None:
        svc = ReleaseService(_auto_register=False)
        result = svc.create(owner="o", repo="r")
        assert "Error" in result

    def test_delete(self, mock_forgejo_client) -> None:  # type: ignore[no-untyped-def]
        mock_forgejo_client.get.return_value = {"id": 42, "tag_name": "v1.0.0"}
        mock_forgejo_client.delete.return_value = None
        svc = ReleaseService(_auto_register=False)
        result = svc.delete(tag="v1.0.0", owner="o", repo="r")
        assert "Deleted" in result

    def test_edit(self, mock_forgejo_client) -> None:  # type: ignore[no-untyped-def]
        mock_forgejo_client.get.return_value = {"id": 42, "tag_name": "v1.0.0"}
        mock_forgejo_client.patch.return_value = {"name": "Updated Release"}
        svc = ReleaseService(_auto_register=False)
        result = svc.edit(tag="v1.0.0", title="Updated Release", owner="o", repo="r")
        assert "Updated Release" in result

    def test_list_infers_context(self, mock_forgejo_client) -> None:  # type: ignore[no-untyped-def]
        mock_forgejo_client.get.return_value = []
        with patch("forge.services.release.get_repo_context", return_value=("o", "r")):
            svc = ReleaseService(_auto_register=False)
            result = svc.list()
            assert "No releases found" in result

    def test_view_infers_context(self, mock_forgejo_client) -> None:  # type: ignore[no-untyped-def]
        mock_forgejo_client.get.return_value = {
            "tag_name": "v1.0",
            "name": "R",
            "author": {"login": "d"},
            "published_at": "",
            "body": "",
            "draft": False,
            "prerelease": False,
            "assets": [],
        }
        with patch("forge.services.release.get_repo_context", return_value=("o", "r")):
            svc = ReleaseService(_auto_register=False)
            result = svc.view(tag="v1.0")
            assert "R" in result

    def test_create_infers_context(self, mock_forgejo_client) -> None:  # type: ignore[no-untyped-def]
        mock_forgejo_client.post.return_value = {"name": "v2.0", "html_url": ""}
        with patch("forge.services.release.get_repo_context", return_value=("o", "r")):
            svc = ReleaseService(_auto_register=False)
            result = svc.create(tag="v2.0")
            assert "v2.0" in result

    def test_create_with_body(self, mock_forgejo_client) -> None:  # type: ignore[no-untyped-def]
        mock_forgejo_client.post.return_value = {"name": "v2.0", "html_url": ""}
        svc = ReleaseService(_auto_register=False)
        result = svc.create(tag="v2.0", body="Notes", owner="o", repo="r")
        assert "v2.0" in result
        call_json = mock_forgejo_client.post.call_args[1]["json"]
        assert call_json["body"] == "Notes"

    def test_delete_infers_context(self, mock_forgejo_client) -> None:  # type: ignore[no-untyped-def]
        mock_forgejo_client.get.return_value = {"id": 1, "tag_name": "v1.0"}
        mock_forgejo_client.delete.return_value = None
        with patch("forge.services.release.get_repo_context", return_value=("o", "r")):
            svc = ReleaseService(_auto_register=False)
            result = svc.delete(tag="v1.0")
            assert "Deleted" in result

    def test_delete_no_tag(self) -> None:
        svc = ReleaseService(_auto_register=False)
        result = svc.delete(owner="o", repo="r")
        assert "Error" in result

    def test_edit_infers_context(self, mock_forgejo_client) -> None:  # type: ignore[no-untyped-def]
        mock_forgejo_client.get.return_value = {"id": 1}
        mock_forgejo_client.patch.return_value = {"name": "E"}
        with patch("forge.services.release.get_repo_context", return_value=("o", "r")):
            svc = ReleaseService(_auto_register=False)
            result = svc.edit(tag="v1.0", title="E")
            assert "E" in result

    def test_edit_no_tag(self) -> None:
        svc = ReleaseService(_auto_register=False)
        result = svc.edit(owner="o", repo="r")
        assert "Error" in result

    def test_edit_with_body(self, mock_forgejo_client) -> None:  # type: ignore[no-untyped-def]
        mock_forgejo_client.get.return_value = {"id": 1}
        mock_forgejo_client.patch.return_value = {"name": "R"}
        svc = ReleaseService(_auto_register=False)
        result = svc.edit(tag="v1.0", body="Updated notes", owner="o", repo="r")
        assert "R" in result
