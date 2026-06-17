"""Tests for the repo service."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from forge.services import repo


class TestRepoService:
    """Tests for repo service functions."""

    def test_list_authenticated_user(self, mock_forgejo_client) -> None:  # type: ignore[no-untyped-def]
        mock_forgejo_client.get.return_value = [
            {
                "full_name": "user/repo1",
                "description": "First repo",
                "stars_count": 5,
                "language": "Python",
            },
        ]
        with patch("forge.services.repo.get_default_owner", return_value=""):
            result = repo.list_repos()
        assert "user/repo1" in result
        mock_forgejo_client.get.assert_called_once_with(
            "/user/repos", params={"limit": 30, "page": 1}
        )

    def test_list_specific_owner(self, mock_forgejo_client) -> None:  # type: ignore[no-untyped-def]
        mock_forgejo_client.get.return_value = [
            {
                "full_name": "alice/proj",
                "description": "",
                "stars_count": 0,
                "language": "Go",
            },
        ]
        result = repo.list_repos(owner="alice")
        assert "alice/proj" in result
        mock_forgejo_client.get.assert_called_once_with(
            "/users/alice/repos", params={"limit": 30, "page": 1}
        )

    def test_list_empty(self, mock_forgejo_client) -> None:  # type: ignore[no-untyped-def]
        mock_forgejo_client.get.return_value = []
        result = repo.list_repos()
        assert "No repositories found" in result

    def test_view(self, mock_forgejo_client) -> None:  # type: ignore[no-untyped-def]
        mock_forgejo_client.get.return_value = {
            "full_name": "owner/repo",
            "description": "A test repo",
            "private": False,
            "stars_count": 42,
            "forks_count": 5,
            "language": "Python",
            "default_branch": "main",
            "html_url": "https://git.example.com/owner/repo",
        }
        result = repo.view(owner="owner", repo="repo")
        assert "owner/repo" in result
        mock_forgejo_client.get.assert_called_once_with("/repos/owner/repo")

    def test_view_infers_context(self, mock_forgejo_client) -> None:  # type: ignore[no-untyped-def]
        mock_forgejo_client.get.return_value = {"full_name": "a/b", "private": False}
        with patch("forge.services.repo.get_repo_context", return_value=("a", "b")):
            result = repo.view()
            assert "a/b" in result

    def test_create(self, mock_forgejo_client) -> None:  # type: ignore[no-untyped-def]
        mock_forgejo_client.post.return_value = {
            "full_name": "user/newrepo",
            "html_url": "https://git.example.com/user/newrepo",
            "clone_url": "https://git.example.com/user/newrepo.git",
        }
        with patch("forge.services.repo.get_default_owner", return_value=""):
            with (
                patch(
                    "forge.services.repo._resolve_remote_name", return_value="origin"
                ) as mock_resolve,
                patch("forge.services.repo._add_remote") as mock_add,
            ):
                result = repo.create(name="newrepo", description="new", private=True)
                mock_resolve.assert_called_once_with("https://git.example.com/user/newrepo.git")
                mock_add.assert_called_once_with(
                    "origin", "https://git.example.com/user/newrepo.git"
                )
        assert "user/newrepo" in result
        mock_forgejo_client.post.assert_called_once_with(
            "/user/repos",
            json={"name": "newrepo", "description": "new", "private": True},
        )

    def test_create_skips_remote_when_resolve_returns_none(self, mock_forgejo_client) -> None:  # type: ignore[no-untyped-def]
        mock_forgejo_client.post.return_value = {
            "full_name": "user/newrepo",
            "html_url": "https://git.example.com/user/newrepo",
            "clone_url": "https://git.example.com/user/newrepo.git",
        }
        with patch("forge.services.repo.get_default_owner", return_value=""):
            with (
                patch("forge.services.repo._resolve_remote_name", return_value=None),
                patch("forge.services.repo._add_remote") as mock_add,
            ):
                result = repo.create(name="newrepo")
                mock_add.assert_not_called()
        assert "user/newrepo" in result

    def test_create_in_org(self, mock_forgejo_client) -> None:  # type: ignore[no-untyped-def]
        mock_forgejo_client.post.return_value = {
            "full_name": "myorg/newrepo",
            "html_url": "https://git.example.com/myorg/newrepo",
            "clone_url": "https://git.example.com/myorg/newrepo.git",
        }
        with (
            patch("forge.services.repo._resolve_remote_name", return_value="origin"),
            patch("forge.services.repo._add_remote"),
        ):
            result = repo.create(name="newrepo", org="myorg")
        assert "myorg/newrepo" in result
        mock_forgejo_client.post.assert_called_once()

    def test_create_defaults_name_to_cwd_basename(self, mock_forgejo_client) -> None:  # type: ignore[no-untyped-def]
        mock_forgejo_client.post.return_value = {
            "full_name": "user/myproject",
            "html_url": "https://git.example.com/user/myproject",
            "clone_url": "https://git.example.com/user/myproject.git",
        }
        with (
            patch("forge.services.repo.os.getcwd", return_value="/home/user/myproject"),
            patch("forge.services.repo.get_default_owner", return_value=""),
            patch("forge.services.repo._resolve_remote_name", return_value="origin"),
            patch("forge.services.repo._add_remote"),
        ):
            result = repo.create()
        assert "myproject" in result
        mock_forgejo_client.post.assert_called_once_with(
            "/user/repos",
            json={"name": "myproject", "description": "", "private": False},
        )

    def test_fork(self, mock_forgejo_client) -> None:  # type: ignore[no-untyped-def]
        mock_forgejo_client.post.return_value = {
            "full_name": "me/forked",
            "html_url": "https://git.example.com/me/forked",
        }
        result = repo.fork(owner="upstream", repo="project")
        assert "me/forked" in result

    def test_delete(self, mock_forgejo_client) -> None:  # type: ignore[no-untyped-def]
        mock_forgejo_client.delete.return_value = None
        result = repo.delete(owner="owner", repo="repo")
        assert "Deleted" in result

    def test_search(self, mock_forgejo_client) -> None:  # type: ignore[no-untyped-def]
        mock_forgejo_client.get.return_value = {
            "data": [
                {
                    "full_name": "user/found",
                    "description": "match",
                    "stars_count": 1,
                    "language": "Rust",
                }
            ]
        }
        result = repo.search(query="found")
        assert "user/found" in result

    def test_search_no_query(self) -> None:
        result = repo.search()
        assert "Error" in result

    def test_create_uses_default_owner(self, mock_forgejo_client) -> None:  # type: ignore[no-untyped-def]
        mock_forgejo_client.post.return_value = {
            "full_name": "default-org/newrepo",
            "html_url": "https://git.example.com/default-org/newrepo",
            "clone_url": "https://git.example.com/default-org/newrepo.git",
        }
        with patch("forge.services.repo.get_default_owner", return_value="default-org"):
            with (
                patch("forge.services.repo._resolve_remote_name", return_value="origin"),
                patch("forge.services.repo._add_remote"),
            ):
                result = repo.create(name="newrepo")
            assert "default-org/newrepo" in result
            mock_forgejo_client.post.assert_called_once_with(
                "/orgs/default-org/repos",
                json={"name": "newrepo", "description": "", "private": False},
            )

    def test_create_explicit_org_overrides_default(self, mock_forgejo_client) -> None:  # type: ignore[no-untyped-def]
        mock_forgejo_client.post.return_value = {
            "full_name": "explicit-org/newrepo",
            "html_url": "https://git.example.com/explicit-org/newrepo",
            "clone_url": "https://git.example.com/explicit-org/newrepo.git",
        }
        with patch("forge.services.repo.get_default_owner", return_value="default-org"):
            with (
                patch("forge.services.repo._resolve_remote_name", return_value="origin"),
                patch("forge.services.repo._add_remote"),
            ):
                result = repo.create(name="newrepo", org="explicit-org")
            assert "explicit-org/newrepo" in result
            mock_forgejo_client.post.assert_called_once_with(
                "/orgs/explicit-org/repos",
                json={"name": "newrepo", "description": "", "private": False},
            )

    def test_list_uses_default_owner(self, mock_forgejo_client) -> None:  # type: ignore[no-untyped-def]
        mock_forgejo_client.get.return_value = [
            {
                "full_name": "default-org/repo1",
                "description": "",
                "stars_count": 0,
                "language": "Python",
            },
        ]
        with patch("forge.services.repo.get_default_owner", return_value="default-org"):
            result = repo.list_repos()
            assert "default-org/repo1" in result
            mock_forgejo_client.get.assert_called_once_with(
                "/users/default-org/repos", params={"limit": 30, "page": 1}
            )

    def test_clone_with_name(self, mock_forgejo_client) -> None:  # type: ignore[no-untyped-def]
        mock_forgejo_client.get.return_value = {
            "full_name": "alice/myrepo",
            "clone_url": "https://git.example.com/alice/myrepo.git",
        }
        with patch("forge.services.repo.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            result = repo.clone(name="myrepo", owner="alice")
        assert "Cloned alice/myrepo into myrepo/" in result
        mock_forgejo_client.get.assert_called_once_with("/repos/alice/myrepo")
        mock_run.assert_called_once_with(
            ["git", "clone", "--", "https://git.example.com/alice/myrepo.git", "myrepo"],
            capture_output=True,
            text=True,
            check=False,
        )

    def test_clone_with_custom_directory(self, mock_forgejo_client) -> None:  # type: ignore[no-untyped-def]
        mock_forgejo_client.get.return_value = {
            "full_name": "alice/myrepo",
            "clone_url": "https://git.example.com/alice/myrepo.git",
        }
        with patch("forge.services.repo.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            result = repo.clone(name="myrepo", owner="alice", directory="custom-dir")
        assert "into custom-dir/" in result
        mock_run.assert_called_once_with(
            ["git", "clone", "--", "https://git.example.com/alice/myrepo.git", "custom-dir"],
            capture_output=True,
            text=True,
            check=False,
        )

    def test_clone_git_error(self, mock_forgejo_client) -> None:  # type: ignore[no-untyped-def]
        mock_forgejo_client.get.return_value = {
            "full_name": "alice/myrepo",
            "clone_url": "https://git.example.com/alice/myrepo.git",
        }
        with patch("forge.services.repo.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=128, stderr="fatal: repository not found")
            result = repo.clone(name="myrepo", owner="alice")
        assert "Error cloning" in result

    def test_clone_no_name_non_interactive(self, mock_forgejo_client) -> None:  # type: ignore[no-untyped-def]
        mock_forgejo_client.get.return_value = [
            {
                "full_name": "alice/repo1",
                "description": "First repo",
            },
        ]
        with patch("forge.services.repo.sys") as mock_sys:
            mock_sys.stdin.isatty.return_value = False
            result = repo.clone(owner="alice")
        assert "repo1" in result

    def test_clone_no_name_interactive(self, mock_forgejo_client) -> None:  # type: ignore[no-untyped-def]
        mock_forgejo_client.get.side_effect = [
            [
                {
                    "full_name": "alice/repo1",
                    "name": "repo1",
                    "description": "First",
                    "owner": {"login": "alice"},
                },
                {
                    "full_name": "alice/repo2",
                    "name": "repo2",
                    "description": "",
                    "owner": {"login": "alice"},
                },
            ],
            {
                "full_name": "alice/repo2",
                "clone_url": "https://git.example.com/alice/repo2.git",
            },
        ]
        with (
            patch("forge.services.repo.sys") as mock_sys,
            patch("forge.services.repo.IntPrompt") as mock_prompt,
            patch("forge.services.repo.subprocess.run") as mock_run,
            patch("forge.services.repo.Console"),
        ):
            mock_sys.stdin.isatty.return_value = True
            mock_prompt.ask.return_value = 2
            mock_run.return_value = MagicMock(returncode=0)
            result = repo.clone(owner="alice")
        assert "Cloned alice/repo2 into repo2/" in result

    def test_clone_no_repos_found(self, mock_forgejo_client) -> None:  # type: ignore[no-untyped-def]
        mock_forgejo_client.get.return_value = []
        result = repo.clone(owner="alice")
        assert "No repositories found" in result

    def test_clone_invalid_selection(self, mock_forgejo_client) -> None:  # type: ignore[no-untyped-def]
        mock_forgejo_client.get.return_value = [
            {
                "full_name": "alice/repo1",
                "name": "repo1",
                "description": "",
                "owner": {"login": "alice"},
            },
        ]
        with (
            patch("forge.services.repo.sys") as mock_sys,
            patch("forge.services.repo.IntPrompt") as mock_prompt,
            patch("forge.services.repo.Console"),
        ):
            mock_sys.stdin.isatty.return_value = True
            mock_prompt.ask.return_value = 99
            result = repo.clone(owner="alice")
        assert "Invalid selection" in result

    def test_clone_uses_default_owner(self, mock_forgejo_client) -> None:  # type: ignore[no-untyped-def]
        mock_forgejo_client.get.return_value = {
            "full_name": "default-org/myrepo",
            "clone_url": "https://git.example.com/default-org/myrepo.git",
        }
        with patch("forge.services.repo.get_default_owner", return_value="default-org"):
            with patch("forge.services.repo.subprocess.run") as mock_run:
                mock_run.return_value = MagicMock(returncode=0)
                result = repo.clone(name="myrepo")
        assert "default-org/myrepo" in result
        mock_forgejo_client.get.assert_called_once_with("/repos/default-org/myrepo")

    def test_resolve_remote_name_no_origin(self) -> None:
        with patch("forge.services.repo._get_existing_origin", return_value=None):
            assert repo._resolve_remote_name("git@example.com:user/repo.git") == "origin"

    def test_resolve_remote_name_origin_exists_overwrite(self) -> None:
        with (
            patch("forge.services.repo._get_existing_origin", return_value="git@old.com:x/y.git"),
            patch("forge.services.repo.sys") as mock_sys,
            patch("forge.services.repo.Prompt") as mock_prompt,
            patch("forge.services.repo.Console"),
        ):
            mock_sys.stdin.isatty.return_value = True
            mock_prompt.ask.return_value = "overwrite"
            result = repo._resolve_remote_name("git@new.com:user/repo.git")
        assert result == "origin"

    def test_resolve_remote_name_origin_exists_different(self) -> None:
        with (
            patch("forge.services.repo._get_existing_origin", return_value="git@old.com:x/y.git"),
            patch("forge.services.repo.sys") as mock_sys,
            patch("forge.services.repo.Prompt") as mock_prompt,
            patch("forge.services.repo.Console"),
        ):
            mock_sys.stdin.isatty.return_value = True
            mock_prompt.ask.side_effect = ["different", "upstream"]
            result = repo._resolve_remote_name("git@new.com:user/repo.git")
        assert result == "upstream"

    def test_resolve_remote_name_origin_exists_skip(self) -> None:
        with (
            patch("forge.services.repo._get_existing_origin", return_value="git@old.com:x/y.git"),
            patch("forge.services.repo.sys") as mock_sys,
            patch("forge.services.repo.Prompt") as mock_prompt,
            patch("forge.services.repo.Console"),
        ):
            mock_sys.stdin.isatty.return_value = True
            mock_prompt.ask.return_value = "skip"
            result = repo._resolve_remote_name("git@new.com:user/repo.git")
        assert result is None

    def test_resolve_remote_name_origin_exists_non_interactive(self) -> None:
        with (
            patch("forge.services.repo._get_existing_origin", return_value="git@old.com:x/y.git"),
            patch("forge.services.repo.sys") as mock_sys,
            patch("forge.services.repo.Console"),
        ):
            mock_sys.stdin.isatty.return_value = False
            result = repo._resolve_remote_name("git@new.com:user/repo.git")
        assert result is None

    def test_fork_uses_default_owner(self, mock_forgejo_client) -> None:  # type: ignore[no-untyped-def]
        mock_forgejo_client.post.return_value = {
            "full_name": "default-org/forked",
            "html_url": "https://git.example.com/default-org/forked",
        }
        with patch("forge.services.repo.get_default_owner", return_value="default-org"):
            result = repo.fork(owner="upstream", repo="project")
            assert "default-org/forked" in result
            mock_forgejo_client.post.assert_called_once_with(
                "/repos/upstream/project/forks",
                json={"organization": "default-org"},
            )
