"""Tests for git remote context detection."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from forge.forgejo.context import get_default_owner, get_repo_context, parse_remote_url


class TestParseRemoteUrl:
    """Tests for parse_remote_url."""

    def test_ssh_url(self) -> None:
        assert parse_remote_url("git@git.example.com:owner/repo.git") == ("owner", "repo")

    def test_ssh_url_no_dot_git(self) -> None:
        assert parse_remote_url("git@git.example.com:owner/repo") == ("owner", "repo")

    def test_https_url(self) -> None:
        assert parse_remote_url("https://git.example.com/owner/repo.git") == ("owner", "repo")

    def test_https_url_no_dot_git(self) -> None:
        assert parse_remote_url("https://git.example.com/owner/repo") == ("owner", "repo")

    def test_https_url_with_port(self) -> None:
        assert parse_remote_url("https://git.example.com:3000/owner/repo.git") == (
            "owner",
            "repo",
        )

    def test_http_url(self) -> None:
        assert parse_remote_url("http://git.example.com/owner/repo.git") == ("owner", "repo")

    def test_invalid_url_raises(self) -> None:
        with pytest.raises(ValueError, match="Cannot parse"):
            parse_remote_url("not-a-url")

    def test_hyphenated_names(self) -> None:
        assert parse_remote_url("git@git.example.com:my-org/my-repo.git") == (
            "my-org",
            "my-repo",
        )

    def test_underscored_names(self) -> None:
        assert parse_remote_url("https://git.example.com/my_org/my_repo") == (
            "my_org",
            "my_repo",
        )


class TestGetRepoContext:
    """Tests for get_repo_context."""

    def test_success(self) -> None:
        with patch("forge.forgejo.context.subprocess") as mock_sp:
            mock_sp.run.return_value.returncode = 0
            mock_sp.run.return_value.stdout = "git@git.example.com:owner/repo.git\n"
            assert get_repo_context() == ("owner", "repo")

    def test_not_in_git_repo_raises(self) -> None:
        with patch("forge.forgejo.context.subprocess") as mock_sp:
            mock_sp.run.return_value.returncode = 128
            mock_sp.run.return_value.stdout = ""
            with pytest.raises(RuntimeError, match="Not in a git repository"):
                get_repo_context()


class TestGetDefaultOwner:
    """Tests for get_default_owner."""

    def test_from_env(self) -> None:
        with patch.dict("os.environ", {"FORGE_FORGEJO__DEFAULT_OWNER": "myorg"}):
            assert get_default_owner() == "myorg"

    def test_from_config(self) -> None:
        with patch.dict("os.environ", {}, clear=False):
            import os
            os.environ.pop("FORGE_FORGEJO__DEFAULT_OWNER", None)
            with patch(
                "click_clop.config.load_config",
                return_value={"forgejo": {"default_owner": "config-org"}},
            ):
                assert get_default_owner() == "config-org"

    def test_empty_when_not_set(self) -> None:
        with patch.dict("os.environ", {}, clear=False):
            import os
            os.environ.pop("FORGE_FORGEJO__DEFAULT_OWNER", None)
            with patch(
                "click_clop.config.load_config",
                return_value={"forgejo": {}},
            ):
                assert get_default_owner() == ""

    def test_env_takes_precedence(self) -> None:
        with patch.dict("os.environ", {"FORGE_FORGEJO__DEFAULT_OWNER": "env-org"}):
            with patch(
                "click_clop.config.load_config",
                return_value={"forgejo": {"default_owner": "config-org"}},
            ):
                assert get_default_owner() == "env-org"
