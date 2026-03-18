"""Tests for git remote context detection."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from forge.forgejo.context import (
    _extract_host,
    _filter_forgejo_remotes,
    _get_forgejo_host,
    _list_remotes,
    get_default_owner,
    get_forge_remote,
    get_repo_context,
    parse_remote_url,
    select_forge_remote,
    set_forge_remote,
)


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


class TestExtractHost:
    """Tests for _extract_host."""

    def test_ssh_url(self) -> None:
        assert _extract_host("git@git.example.com:owner/repo.git") == "git.example.com"

    def test_https_url(self) -> None:
        assert _extract_host("https://git.example.com/owner/repo.git") == "git.example.com"

    def test_https_url_with_port(self) -> None:
        assert _extract_host("https://git.example.com:3000/owner/repo.git") == "git.example.com"

    def test_http_url(self) -> None:
        assert _extract_host("http://git.example.com/owner/repo") == "git.example.com"

    def test_empty_string(self) -> None:
        assert _extract_host("") == ""

    def test_invalid_url(self) -> None:
        assert _extract_host("not-a-url") == ""


class TestGetForgejoHost:
    """Tests for _get_forgejo_host."""

    def test_from_env(self) -> None:
        with patch.dict(
            "os.environ", {"FORGE_FORGEJO__URL": "https://git.example.com"}
        ):
            assert _get_forgejo_host() == "git.example.com"

    def test_from_config(self) -> None:
        with patch.dict("os.environ", {}, clear=False):
            import os

            os.environ.pop("FORGE_FORGEJO__URL", None)
            with patch(
                "forge.config.get_config",
                return_value={"forgejo": {"url": "https://forgejo.local"}},
            ):
                assert _get_forgejo_host() == "forgejo.local"

    def test_env_takes_precedence(self) -> None:
        with patch.dict(
            "os.environ", {"FORGE_FORGEJO__URL": "https://env.example.com"}
        ):
            with patch(
                "forge.config.get_config",
                return_value={"forgejo": {"url": "https://config.example.com"}},
            ):
                assert _get_forgejo_host() == "env.example.com"

    def test_empty_when_not_configured(self) -> None:
        with patch.dict("os.environ", {}, clear=False):
            import os

            os.environ.pop("FORGE_FORGEJO__URL", None)
            with patch(
                "forge.config.get_config",
                return_value={"forgejo": {}},
            ):
                assert _get_forgejo_host() == ""


class TestFilterForgejoRemotes:
    """Tests for _filter_forgejo_remotes."""

    def test_filters_to_matching_remotes(self) -> None:
        with patch(
            "forge.forgejo.context._get_forgejo_host", return_value="git.example.com"
        ):
            with patch("forge.forgejo.context._get_remote_url") as mock_url:
                mock_url.side_effect = lambda name: {
                    "origin": "git@github.com:user/repo.git",
                    "forge": "git@git.example.com:user/repo.git",
                }[name]
                result = _filter_forgejo_remotes(["origin", "forge"])
                assert result == ["forge"]

    def test_returns_all_when_no_host_configured(self) -> None:
        with patch("forge.forgejo.context._get_forgejo_host", return_value=""):
            result = _filter_forgejo_remotes(["origin", "upstream"])
            assert result == ["origin", "upstream"]

    def test_returns_empty_when_none_match(self) -> None:
        with patch(
            "forge.forgejo.context._get_forgejo_host", return_value="git.example.com"
        ):
            with patch("forge.forgejo.context._get_remote_url") as mock_url:
                mock_url.return_value = "git@github.com:user/repo.git"
                result = _filter_forgejo_remotes(["origin", "upstream"])
                assert result == []

    def test_case_insensitive_host_match(self) -> None:
        with patch(
            "forge.forgejo.context._get_forgejo_host", return_value="Git.Example.COM"
        ):
            with patch(
                "forge.forgejo.context._get_remote_url",
                return_value="git@git.example.com:user/repo.git",
            ):
                result = _filter_forgejo_remotes(["origin"])
                assert result == ["origin"]

    def test_matches_https_remote(self) -> None:
        with patch(
            "forge.forgejo.context._get_forgejo_host", return_value="git.example.com"
        ):
            with patch(
                "forge.forgejo.context._get_remote_url",
                return_value="https://git.example.com/user/repo.git",
            ):
                result = _filter_forgejo_remotes(["origin"])
                assert result == ["origin"]


class TestGetForgeRemote:
    """Tests for get_forge_remote."""

    def test_returns_remote_name(self) -> None:
        with patch("forge.forgejo.context.subprocess") as mock_sp:
            mock_sp.run.return_value.returncode = 0
            mock_sp.run.return_value.stdout = "remote.upstream.forge true\n"
            assert get_forge_remote() == "upstream"

    def test_returns_none_when_not_configured(self) -> None:
        with patch("forge.forgejo.context.subprocess") as mock_sp:
            mock_sp.run.return_value.returncode = 1
            mock_sp.run.return_value.stdout = ""
            assert get_forge_remote() is None

    def test_returns_none_on_empty_output(self) -> None:
        with patch("forge.forgejo.context.subprocess") as mock_sp:
            mock_sp.run.return_value.returncode = 0
            mock_sp.run.return_value.stdout = ""
            assert get_forge_remote() is None

    def test_picks_first_if_multiple(self) -> None:
        with patch("forge.forgejo.context.subprocess") as mock_sp:
            mock_sp.run.return_value.returncode = 0
            mock_sp.run.return_value.stdout = (
                "remote.upstream.forge true\nremote.origin.forge true\n"
            )
            assert get_forge_remote() == "upstream"


class TestSetForgeRemote:
    """Tests for set_forge_remote."""

    def test_sets_new_forge_remote(self) -> None:
        with patch("forge.forgejo.context.get_forge_remote", return_value=None):
            with patch("forge.forgejo.context.subprocess") as mock_sp:
                mock_sp.run.return_value.returncode = 0
                set_forge_remote("upstream")
                mock_sp.run.assert_called_once_with(
                    ["git", "config", "remote.upstream.forge", "true"],
                    capture_output=True,
                    check=True,
                )

    def test_clears_old_before_setting_new(self) -> None:
        with patch("forge.forgejo.context.get_forge_remote", return_value="origin"):
            with patch("forge.forgejo.context.subprocess") as mock_sp:
                mock_sp.run.return_value.returncode = 0
                set_forge_remote("upstream")
                assert mock_sp.run.call_count == 2
                mock_sp.run.assert_any_call(
                    ["git", "config", "--unset", "remote.origin.forge"],
                    capture_output=True,
                    check=False,
                )
                mock_sp.run.assert_any_call(
                    ["git", "config", "remote.upstream.forge", "true"],
                    capture_output=True,
                    check=True,
                )


class TestListRemotes:
    """Tests for _list_remotes."""

    def test_returns_remote_names(self) -> None:
        with patch("forge.forgejo.context.subprocess") as mock_sp:
            mock_sp.run.return_value.returncode = 0
            mock_sp.run.return_value.stdout = "origin\nupstream\n"
            assert _list_remotes() == ["origin", "upstream"]

    def test_returns_empty_on_failure(self) -> None:
        with patch("forge.forgejo.context.subprocess") as mock_sp:
            mock_sp.run.return_value.returncode = 128
            mock_sp.run.return_value.stdout = ""
            assert _list_remotes() == []


class TestSelectForgeRemote:
    """Tests for select_forge_remote."""

    def test_auto_selects_single_forgejo_remote(self) -> None:
        with (
            patch("forge.forgejo.context._list_remotes", return_value=["origin"]),
            patch(
                "forge.forgejo.context._filter_forgejo_remotes",
                return_value=["origin"],
            ),
            patch("forge.forgejo.context.set_forge_remote") as mock_set,
        ):
            result = select_forge_remote()
            assert result == "origin"
            mock_set.assert_called_once_with("origin")

    def test_raises_with_no_remotes(self) -> None:
        with patch("forge.forgejo.context._list_remotes", return_value=[]):
            with pytest.raises(RuntimeError, match="No git remotes configured"):
                select_forge_remote()

    def test_raises_when_no_remotes_match_forgejo(self) -> None:
        with (
            patch(
                "forge.forgejo.context._list_remotes",
                return_value=["origin", "upstream"],
            ),
            patch("forge.forgejo.context._filter_forgejo_remotes", return_value=[]),
            patch(
                "forge.forgejo.context._get_forgejo_host",
                return_value="git.example.com",
            ),
            patch("forge.forgejo.context._get_remote_url") as mock_url,
        ):
            mock_url.side_effect = lambda name: {
                "origin": "git@github.com:u/r.git",
                "upstream": "git@gitlab.com:u/r.git",
            }.get(name, "")
            with pytest.raises(
                RuntimeError, match="No remotes point to the Forgejo instance"
            ):
                select_forge_remote()

    def test_non_interactive_falls_back_to_origin(self) -> None:
        with (
            patch(
                "forge.forgejo.context._list_remotes",
                return_value=["upstream", "origin"],
            ),
            patch(
                "forge.forgejo.context._filter_forgejo_remotes",
                return_value=["upstream", "origin"],
            ),
            patch("forge.forgejo.context.set_forge_remote") as mock_set,
            patch("forge.forgejo.context.sys") as mock_sys,
        ):
            mock_sys.stdin.isatty.return_value = False
            result = select_forge_remote()
            assert result == "origin"
            mock_set.assert_called_once_with("origin")

    def test_non_interactive_falls_back_to_first_forgejo_remote(self) -> None:
        with (
            patch(
                "forge.forgejo.context._list_remotes",
                return_value=["upstream", "fork"],
            ),
            patch(
                "forge.forgejo.context._filter_forgejo_remotes",
                return_value=["upstream", "fork"],
            ),
            patch("forge.forgejo.context.set_forge_remote") as mock_set,
            patch("forge.forgejo.context.sys") as mock_sys,
        ):
            mock_sys.stdin.isatty.return_value = False
            result = select_forge_remote()
            assert result == "upstream"
            mock_set.assert_called_once_with("upstream")

    def test_interactive_prompts_user(self) -> None:
        with (
            patch(
                "forge.forgejo.context._list_remotes",
                return_value=["origin", "upstream"],
            ),
            patch(
                "forge.forgejo.context._filter_forgejo_remotes",
                return_value=["origin", "upstream"],
            ),
            patch("forge.forgejo.context.set_forge_remote") as mock_set,
            patch("forge.forgejo.context.sys") as mock_sys,
            patch(
                "forge.forgejo.context._get_remote_url",
                return_value="git@example.com:o/r.git",
            ),
            patch("forge.forgejo.context.IntPrompt") as mock_prompt,
            patch("forge.forgejo.context.Console"),
        ):
            mock_sys.stdin.isatty.return_value = True
            mock_prompt.ask.return_value = 2
            result = select_forge_remote()
            assert result == "upstream"
            mock_set.assert_called_once_with("upstream")

    def test_auto_selects_only_forgejo_remote_among_many(self) -> None:
        """If multiple remotes exist but only one points to Forgejo, auto-select it."""
        with (
            patch(
                "forge.forgejo.context._list_remotes",
                return_value=["origin", "forge"],
            ),
            patch(
                "forge.forgejo.context._filter_forgejo_remotes",
                return_value=["forge"],
            ),
            patch("forge.forgejo.context.set_forge_remote") as mock_set,
        ):
            result = select_forge_remote()
            assert result == "forge"
            mock_set.assert_called_once_with("forge")


class TestGetRepoContext:
    """Tests for get_repo_context."""

    def test_uses_saved_forge_remote(self) -> None:
        with (
            patch("forge.forgejo.context.get_forge_remote", return_value="upstream"),
            patch("forge.forgejo.context._is_forgejo_remote", return_value=True),
            patch("forge.forgejo.context.subprocess") as mock_sp,
        ):
            mock_sp.run.return_value.returncode = 0
            mock_sp.run.return_value.stdout = "git@git.example.com:owner/repo.git\n"
            assert get_repo_context() == ("owner", "repo")
            mock_sp.run.assert_called_once_with(
                ["git", "remote", "get-url", "upstream"],
                capture_output=True,
                text=True,
                check=False,
            )

    def test_selects_remote_on_first_use(self) -> None:
        with (
            patch("forge.forgejo.context.get_forge_remote", return_value=None),
            patch(
                "forge.forgejo.context.select_forge_remote", return_value="origin"
            ),
            patch("forge.forgejo.context.subprocess") as mock_sp,
        ):
            mock_sp.run.return_value.returncode = 0
            mock_sp.run.return_value.stdout = (
                "git@git.example.com:owner/repo.git\n"
            )
            assert get_repo_context() == ("owner", "repo")

    def test_remote_not_found_raises(self) -> None:
        with (
            patch("forge.forgejo.context.get_forge_remote", return_value="gone"),
            patch("forge.forgejo.context._is_forgejo_remote", return_value=True),
            patch("forge.forgejo.context.subprocess") as mock_sp,
        ):
            mock_sp.run.return_value.returncode = 128
            mock_sp.run.return_value.stdout = ""
            with pytest.raises(RuntimeError, match="remote 'gone' not configured"):
                get_repo_context()

    def test_reselects_when_saved_remote_not_forgejo(self) -> None:
        """If saved remote no longer points to Forgejo, clear it and re-select."""
        with (
            patch("forge.forgejo.context.get_forge_remote", return_value="origin"),
            patch("forge.forgejo.context._is_forgejo_remote", return_value=False),
            patch("forge.forgejo.context._get_remote_url", return_value="git@github.com:u/r.git"),
            patch("forge.forgejo.context._get_forgejo_host", return_value="git.example.com"),
            patch("forge.forgejo.context.subprocess") as mock_sp,
            patch(
                "forge.forgejo.context.select_forge_remote", return_value="forge"
            ),
            patch("forge.forgejo.context.Console"),
        ):
            mock_sp.run.return_value.returncode = 0
            mock_sp.run.return_value.stdout = (
                "git@git.example.com:owner/repo.git\n"
            )
            assert get_repo_context() == ("owner", "repo")
            # Should have unset the old forge flag
            mock_sp.run.assert_any_call(
                ["git", "config", "--unset", "remote.origin.forge"],
                capture_output=True,
                check=False,
            )


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
                "forge.config.get_config",
                return_value={"forgejo": {"default_owner": "config-org"}},
            ):
                assert get_default_owner() == "config-org"

    def test_empty_when_not_set(self) -> None:
        with patch.dict("os.environ", {}, clear=False):
            import os
            os.environ.pop("FORGE_FORGEJO__DEFAULT_OWNER", None)
            with patch(
                "forge.config.get_config",
                return_value={"forgejo": {}},
            ):
                assert get_default_owner() == ""

    def test_env_takes_precedence(self) -> None:
        with patch.dict("os.environ", {"FORGE_FORGEJO__DEFAULT_OWNER": "env-org"}):
            with patch(
                "forge.config.get_config",
                return_value={"forgejo": {"default_owner": "config-org"}},
            ):
                assert get_default_owner() == "env-org"
