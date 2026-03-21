"""Forgejo container fixture for integration tests.

Manages a real Forgejo instance running in a podman/docker container.
Provides helpers to create users, tokens, and verify API state.
"""

from __future__ import annotations

import os
import socket
import subprocess
import time
from dataclasses import dataclass

import httpx


@dataclass
class ForgejoInstance:
    """A running Forgejo test instance."""

    url: str
    admin_user: str
    admin_password: str
    admin_token: str
    container_id: str
    _runtime: str = "podman"

    def api_get(self, path: str) -> dict | list:
        """GET a Forgejo API endpoint."""
        resp = httpx.get(
            f"{self.url}/api/v1{path}",
            headers={"Authorization": f"token {self.admin_token}"},
            timeout=10.0,
        )
        resp.raise_for_status()
        if resp.status_code == 204 or not resp.content:
            return {}
        return resp.json()

    def api_post(self, path: str, json_data: dict | None = None) -> dict:
        """POST to a Forgejo API endpoint."""
        resp = httpx.post(
            f"{self.url}/api/v1{path}",
            headers={"Authorization": f"token {self.admin_token}"},
            json=json_data or {},
            timeout=10.0,
        )
        resp.raise_for_status()
        if resp.status_code == 204 or not resp.content:
            return {}
        return resp.json()

    def api_delete(self, path: str) -> None:
        """DELETE a Forgejo API endpoint."""
        resp = httpx.delete(
            f"{self.url}/api/v1{path}",
            headers={"Authorization": f"token {self.admin_token}"},
            timeout=10.0,
        )
        resp.raise_for_status()

    def api_patch(self, path: str, json_data: dict | None = None) -> dict:
        """PATCH a Forgejo API endpoint."""
        resp = httpx.patch(
            f"{self.url}/api/v1{path}",
            headers={"Authorization": f"token {self.admin_token}"},
            json=json_data or {},
            timeout=10.0,
        )
        resp.raise_for_status()
        if resp.status_code == 204 or not resp.content:
            return {}
        return resp.json()

    def stop(self) -> None:
        """Stop and remove the container."""
        subprocess.run(
            [self._runtime, "rm", "-f", self.container_id],
            capture_output=True,
            check=False,
        )


def _find_free_port() -> int:
    """Find an available TCP port."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("", 0))
        return s.getsockname()[1]


def _find_runtime() -> str:
    """Find podman or docker."""
    for rt in ("podman", "docker"):
        result = subprocess.run([rt, "--version"], capture_output=True, check=False)
        if result.returncode == 0:
            return rt
    raise RuntimeError("Neither podman nor docker found")


def start_forgejo(
    image: str = "codeberg.org/forgejo/forgejo:11",
    port: int = 0,
    admin_user: str = "testadmin",
    admin_password: str = "testpassword123!",
    admin_email: str = "admin@test.local",
) -> ForgejoInstance:
    """Start a Forgejo container and return a ready-to-use instance.

    Args:
        image: Container image to use.
        port: Host port to bind (0 = random).
        admin_user: Admin username to create.
        admin_password: Admin password.
        admin_email: Admin email.
    """
    runtime = _find_runtime()

    # Find a free port
    if not port:
        port = _find_free_port()

    # Start the container
    result = subprocess.run(
        [
            runtime,
            "run",
            "-d",
            "--name",
            f"forge-test-{os.getpid()}",
            "-p",
            f"{port}:3000",
            "-e",
            "FORGEJO__security__INSTALL_LOCK=true",
            "-e",
            f"FORGEJO__server__ROOT_URL=http://localhost:{port}",
            "-e",
            "FORGEJO__database__DB_TYPE=sqlite3",
            "-e",
            "FORGEJO__server__DISABLE_SSH=true",
            image,
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    container_id = result.stdout.strip()
    base_url = f"http://localhost:{port}"

    # Wait for Forgejo to be ready
    _wait_for_ready(base_url, timeout=60)

    # Create admin user via forgejo CLI inside container (as git user, not root)
    subprocess.run(
        [
            runtime,
            "exec",
            "--user",
            "git",
            container_id,
            "forgejo",
            "admin",
            "user",
            "create",
            "--admin",
            "--username",
            admin_user,
            "--password",
            admin_password,
            "--email",
            admin_email,
            "--must-change-password=false",
        ],
        capture_output=True,
        text=True,
        check=True,
    )

    # Create an API token via the API (using basic auth first)
    token_resp = httpx.post(
        f"{base_url}/api/v1/users/{admin_user}/tokens",
        auth=(admin_user, admin_password),
        json={"name": "test-token", "scopes": ["all"]},
        timeout=10.0,
    )
    token_resp.raise_for_status()
    token = token_resp.json()["sha1"]

    return ForgejoInstance(
        url=base_url,
        admin_user=admin_user,
        admin_password=admin_password,
        admin_token=token,
        container_id=container_id,
        _runtime=runtime,
    )


def _wait_for_ready(url: str, timeout: int = 60) -> None:
    """Poll until Forgejo responds to health checks."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            resp = httpx.get(f"{url}/api/v1/version", timeout=2.0)
            if resp.status_code == 200:
                return
        except (
            httpx.ConnectError,
            httpx.ReadTimeout,
            httpx.ReadError,
            httpx.RemoteProtocolError,
            ConnectionResetError,
            OSError,
        ):
            pass
        time.sleep(1)
    raise TimeoutError(f"Forgejo did not become ready at {url} within {timeout}s")
