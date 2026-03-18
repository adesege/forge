"""Forgejo API client — synchronous httpx wrapper."""

from __future__ import annotations

from typing import Any

import httpx

from forge.forgejo.exceptions import (
    ForgejoAPIError,
    ForgejoAuthError,
    ForgejoNotFoundError,
    ForgejoValidationError,
)


class ForgejoClient:
    """Synchronous HTTP client for the Forgejo API v1."""

    def __init__(self, base_url: str, token: str) -> None:
        self._base_url = base_url.rstrip("/")
        api_base = self._base_url + "/api/v1"
        self._token = token
        self._client = httpx.Client(
            base_url=api_base,
            headers={
                "Authorization": f"token {token}",
                "Accept": "application/json",
                "Content-Type": "application/json",
            },
            timeout=30.0,
        )

    def _handle_response(self, response: httpx.Response) -> Any:
        """Check response status and return parsed JSON (or None for 204)."""
        if response.status_code == 204:
            return None
        if response.status_code == 404:
            msg = self._extract_message(response)
            raise ForgejoNotFoundError(msg)
        if response.status_code in (401, 403):
            msg = self._extract_message(response)
            raise ForgejoAuthError(msg)
        if response.status_code == 422:
            msg = self._extract_message(response)
            raise ForgejoValidationError(msg)
        if response.status_code >= 400:
            msg = self._extract_message(response)
            raise ForgejoAPIError(response.status_code, msg)
        if not response.content:
            return None
        return response.json()

    @staticmethod
    def _extract_message(response: httpx.Response) -> str:
        """Extract error message from response body."""
        try:
            data = response.json()
            return str(data.get("message", response.text))
        except Exception:
            return response.text

    def get(self, path: str, params: dict[str, Any] | None = None) -> Any:
        """Send a GET request."""
        resp = self._client.get(path, params=params)
        return self._handle_response(resp)

    def post(self, path: str, json: dict[str, Any] | None = None) -> Any:
        """Send a POST request."""
        resp = self._client.post(path, json=json)
        return self._handle_response(resp)

    def patch(self, path: str, json: dict[str, Any] | None = None) -> Any:
        """Send a PATCH request."""
        resp = self._client.patch(path, json=json)
        return self._handle_response(resp)

    def delete(self, path: str) -> Any:
        """Send a DELETE request."""
        resp = self._client.delete(path)
        return self._handle_response(resp)

    def get_raw(self, path: str, accept: str = "text/plain") -> str:
        """Send a GET request and return raw text (for diffs, patches)."""
        resp = self._client.get(path, headers={"Accept": accept})
        if resp.status_code >= 400:
            self._handle_response(resp)
        return resp.text

    def get_paginated(
        self,
        path: str,
        params: dict[str, Any] | None = None,
        limit: int = 30,
    ) -> list[Any]:
        """Fetch all pages up to limit items."""
        params = dict(params) if params else {}
        page_size = min(limit, 50)
        params["limit"] = page_size
        params["page"] = 1
        results: list[Any] = []

        while len(results) < limit:
            data = self.get(path, params=params)
            if not data:
                break
            results.extend(data)
            if len(data) < page_size:
                break
            params["page"] += 1

        return results[:limit]

    def put_file(
        self,
        path: str,
        content: bytes,
        content_type: str = "application/octet-stream",
    ) -> Any:
        """Upload a file via PUT to a non-v1 API path (e.g. package registry).

        The path should start with /api/packages/... (not /api/v1/).
        """
        url = self._base_url + path
        resp = self._client.put(
            url,
            content=content,
            headers={
                "Content-Type": content_type,
                "Authorization": f"token {self._token}",
            },
        )
        return self._handle_response(resp)

    def download_file(self, path: str) -> bytes:
        """Download binary content from a non-v1 API path.

        The path should start with /api/packages/... (not /api/v1/).
        """
        url = self._base_url + path
        resp = self._client.get(
            url,
            headers={
                "Accept": "application/octet-stream",
                "Authorization": f"token {self._token}",
            },
        )
        if resp.status_code >= 400:
            self._handle_response(resp)
        return resp.content

    def close(self) -> None:
        """Close the underlying HTTP client."""
        self._client.close()


# --- Module-level factory ---

_client: ForgejoClient | None = None


def get_client() -> ForgejoClient:
    """Return a lazily-initialized ForgejoClient using config.

    Token resolution order:
    1. FORGE_FORGEJO__TOKEN env var
    2. config["forgejo"]["token"] (e.g. config.local.toml)
    3. 1Password via op read (config["forgejo"]["token_op_ref"])
    """
    global _client  # noqa: PLW0603
    if _client is not None:
        return _client

    import os

    from forge.config import get_config

    config = get_config()
    forgejo_cfg = config.get("forgejo", {})

    url = os.environ.get("FORGE_FORGEJO__URL", forgejo_cfg.get("url", ""))
    if not url:
        raise RuntimeError(
            "Forgejo URL not configured. Set FORGE_FORGEJO__URL or [forgejo] url in config.toml"
        )

    token = os.environ.get("FORGE_FORGEJO__TOKEN", forgejo_cfg.get("token", ""))
    if not token:
        op_ref = forgejo_cfg.get("token_op_ref", "")
        if op_ref:
            import subprocess

            result = subprocess.run(
                ["op", "read", op_ref],
                capture_output=True,
                text=True,
                check=False,
            )
            if result.returncode == 0:
                token = result.stdout.strip()

    if not token:
        raise RuntimeError(
            "Forgejo token not configured. Set FORGE_FORGEJO__TOKEN, "
            "[forgejo] token in config.local.toml, or [forgejo] token_op_ref for 1Password"
        )

    _client = ForgejoClient(url, token)
    return _client


def reset_client() -> None:
    """Reset the cached client (for testing)."""
    global _client  # noqa: PLW0603
    _client = None
