"""Tests for the secrets service."""

from __future__ import annotations

from unittest.mock import patch

from forge import secrets


class TestSecretsService:
    """Tests for secrets service functions."""

    def test_status_available(self) -> None:
        with patch("forge.secrets.check_op_available", return_value=True):
            result = secrets.status()
            assert "available and authenticated" in result

    def test_status_not_available(self) -> None:
        with patch("forge.secrets.check_op_available", return_value=False):
            result = secrets.status()
            assert "not available" in result

    def test_get_with_field(self) -> None:
        with patch("forge.secrets.get_secret_field", return_value="secret-value"):
            result = secrets.get(vault="myvault", title="myitem", field="password")
            assert result == "secret-value"

    def test_get_full_item(self) -> None:
        item = {"id": "123", "fields": [{"label": "password", "value": "secret"}]}
        with patch("forge.secrets.get_secret", return_value=item):
            result = secrets.get(vault="myvault", title="myitem")
            assert '"id": "123"' in result

    def test_create(self) -> None:
        created = {"id": "456", "title": "newitem"}
        with patch("forge.secrets.create_secret", return_value=created) as mock_create:
            result = secrets.create(vault="myvault", title="newitem", key="api_key", value="abc123")
            assert '"id": "456"' in result
            mock_create.assert_called_once()
            args = mock_create.call_args
            assert args[0][0] == "myvault"
            assert args[0][1] == "newitem"

    def test_ensure(self) -> None:
        ensured = {"id": "789", "title": "item"}
        with patch("forge.secrets.ensure_secret", return_value=ensured) as mock_ensure:
            result = secrets.ensure(vault="myvault", title="item", key="token", value="xyz")
            assert '"id": "789"' in result
            mock_ensure.assert_called_once()

    def test_remove(self) -> None:
        with patch("forge.secrets.delete_secret") as mock_delete:
            result = secrets.remove(vault="myvault", title="olditem")
            assert "Deleted" in result
            assert "olditem" in result
            mock_delete.assert_called_once_with("myvault", "olditem")
