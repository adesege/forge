"""Tests for the auth service."""

from __future__ import annotations

from unittest.mock import patch

from forge.services import auth


class TestAuthService:
    """Tests for auth service functions."""

    def test_status_returns_user_info(self, mock_forgejo_client) -> None:  # type: ignore[no-untyped-def]
        mock_forgejo_client.get.return_value = {
            "login": "testuser",
            "full_name": "Test User",
            "email": "test@example.com",
            "is_admin": False,
        }
        result = auth.status()
        assert "testuser" in result
        mock_forgejo_client.get.assert_called_once_with("/user")

    def test_token_from_env(self) -> None:
        with (
            patch.dict("os.environ", {"FORGE_FORGEJO__TOKEN": "secret1234567890"}),
            patch(
                "forge.config.load_config",
                return_value={"forgejo": {"token": ""}},
            ),
        ):
            result = auth.token()
            assert "****7890" in result
            assert "environment variable" in result

    def test_token_masked(self) -> None:
        with (
            patch.dict("os.environ", {}, clear=True),
            patch(
                "forge.config.load_config",
                return_value={"forgejo": {"token": "abcdef1234"}},
            ),
        ):
            result = auth.token()
            assert "****1234" in result
            assert "config file" in result

    def test_token_not_configured(self) -> None:
        with (
            patch.dict("os.environ", {}, clear=True),
            patch(
                "forge.config.load_config",
                return_value={"forgejo": {}},
            ),
        ):
            result = auth.token()
            assert "No token configured" in result
