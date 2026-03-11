"""Tests for the Forgejo API client."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import httpx
import pytest

from forge.forgejo.client import ForgejoClient, get_client, reset_client
from forge.forgejo.exceptions import (
    ForgejoAPIError,
    ForgejoAuthError,
    ForgejoNotFoundError,
    ForgejoValidationError,
)


@pytest.fixture
def client() -> ForgejoClient:
    """Create a client with a mock transport."""
    return ForgejoClient("https://git.example.com", "test-token")


class TestForgejoClient:
    """Tests for ForgejoClient HTTP methods."""

    def test_init_sets_base_url_and_headers(self) -> None:
        client = ForgejoClient("https://git.example.com/", "mytoken")
        assert "git.example.com/api/v1" in str(client._client.base_url)
        assert client._client.headers["authorization"] == "token mytoken"

    def test_init_strips_trailing_slash(self) -> None:
        client = ForgejoClient("https://git.example.com///", "tok")
        assert "git.example.com/api/v1" in str(client._client.base_url)
        # Should not contain triple slashes
        assert "///" not in str(client._client.base_url)

    def test_handle_response_404_raises_not_found(self, client: ForgejoClient) -> None:
        response = httpx.Response(404, json={"message": "not found"})
        with pytest.raises(ForgejoNotFoundError):
            client._handle_response(response)

    def test_handle_response_401_raises_auth_error(self, client: ForgejoClient) -> None:
        response = httpx.Response(401, json={"message": "unauthorized"})
        with pytest.raises(ForgejoAuthError):
            client._handle_response(response)

    def test_handle_response_403_raises_auth_error(self, client: ForgejoClient) -> None:
        response = httpx.Response(403, json={"message": "forbidden"})
        with pytest.raises(ForgejoAuthError):
            client._handle_response(response)

    def test_handle_response_422_raises_validation_error(self, client: ForgejoClient) -> None:
        response = httpx.Response(422, json={"message": "invalid"})
        with pytest.raises(ForgejoValidationError):
            client._handle_response(response)

    def test_handle_response_500_raises_api_error(self, client: ForgejoClient) -> None:
        response = httpx.Response(500, json={"message": "server error"})
        with pytest.raises(ForgejoAPIError):
            client._handle_response(response)

    def test_handle_response_204_returns_none(self, client: ForgejoClient) -> None:
        response = httpx.Response(204)
        assert client._handle_response(response) is None

    def test_handle_response_200_returns_json(self, client: ForgejoClient) -> None:
        response = httpx.Response(200, json={"id": 1, "name": "test"})
        assert client._handle_response(response) == {"id": 1, "name": "test"}

    def test_handle_response_200_empty_body_returns_none(self, client: ForgejoClient) -> None:
        response = httpx.Response(200)
        assert client._handle_response(response) is None

    def test_get_calls_client_get(self, client: ForgejoClient) -> None:
        mock_resp = httpx.Response(200, json=[{"id": 1}])
        client._client = MagicMock()
        client._client.get.return_value = mock_resp
        result = client.get("/repos", params={"limit": 10})
        client._client.get.assert_called_once_with("/repos", params={"limit": 10})
        assert result == [{"id": 1}]

    def test_post_calls_client_post(self, client: ForgejoClient) -> None:
        mock_resp = httpx.Response(201, json={"id": 1})
        client._client = MagicMock()
        client._client.post.return_value = mock_resp
        result = client.post("/repos", json={"name": "test"})
        client._client.post.assert_called_once_with("/repos", json={"name": "test"})
        assert result == {"id": 1}

    def test_patch_calls_client_patch(self, client: ForgejoClient) -> None:
        mock_resp = httpx.Response(200, json={"id": 1})
        client._client = MagicMock()
        client._client.patch.return_value = mock_resp
        result = client.patch("/repos/1", json={"name": "new"})
        client._client.patch.assert_called_once_with("/repos/1", json={"name": "new"})
        assert result == {"id": 1}

    def test_delete_calls_client_delete(self, client: ForgejoClient) -> None:
        mock_resp = httpx.Response(204)
        client._client = MagicMock()
        client._client.delete.return_value = mock_resp
        result = client.delete("/repos/1")
        client._client.delete.assert_called_once_with("/repos/1")
        assert result is None

    def test_get_paginated_collects_pages(self, client: ForgejoClient) -> None:
        page1 = [{"id": i} for i in range(50)]
        page2 = [{"id": i} for i in range(50, 80)]
        client._client = MagicMock()
        client._client.get.side_effect = [
            httpx.Response(200, json=page1),
            httpx.Response(200, json=page2),
        ]
        result = client.get_paginated("/repos", limit=100)
        assert len(result) == 80

    def test_get_paginated_respects_limit(self, client: ForgejoClient) -> None:
        page1 = [{"id": i} for i in range(50)]
        page2 = [{"id": i} for i in range(50, 100)]
        client._client = MagicMock()
        client._client.get.side_effect = [
            httpx.Response(200, json=page1),
            httpx.Response(200, json=page2),
        ]
        result = client.get_paginated("/repos", limit=60)
        assert len(result) == 60

    def test_get_paginated_stops_on_empty(self, client: ForgejoClient) -> None:
        client._client = MagicMock()
        client._client.get.side_effect = [
            httpx.Response(200, json=[{"id": 1}]),
            httpx.Response(200, json=[]),
        ]
        result = client.get_paginated("/repos", limit=100)
        assert len(result) == 1


class TestGetClient:
    """Tests for the get_client factory function."""

    def setup_method(self) -> None:
        reset_client()

    def teardown_method(self) -> None:
        reset_client()

    def test_get_client_from_env(self) -> None:
        with (
            patch.dict(
                "os.environ",
                {"FORGE_FORGEJO__URL": "https://git.test.com", "FORGE_FORGEJO__TOKEN": "tok123"},
            ),
            patch("click_clop.config.load_config", return_value={}),
        ):
            client = get_client()
            assert isinstance(client, ForgejoClient)

    def test_get_client_missing_url_raises(self) -> None:
        with (
            patch.dict("os.environ", {}, clear=True),
            patch("click_clop.config.load_config", return_value={}),
        ):
            with pytest.raises(RuntimeError, match="URL not configured"):
                get_client()

    def test_get_client_missing_token_raises(self) -> None:
        with (
            patch.dict(
                "os.environ", {"FORGE_FORGEJO__URL": "https://git.test.com"}, clear=True
            ),
            patch("click_clop.config.load_config", return_value={"forgejo": {"url": ""}}),
        ):
            with pytest.raises(RuntimeError, match="token not configured"):
                get_client()

    def test_get_client_returns_cached_instance(self) -> None:
        with (
            patch.dict(
                "os.environ",
                {"FORGE_FORGEJO__URL": "https://git.test.com", "FORGE_FORGEJO__TOKEN": "tok"},
            ),
            patch("click_clop.config.load_config", return_value={}),
        ):
            c1 = get_client()
            c2 = get_client()
            assert c1 is c2
