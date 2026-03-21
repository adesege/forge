"""Install service — configure package repositories for forge."""

from __future__ import annotations

import os
import subprocess
import tomllib
from pathlib import Path
from urllib.parse import urlparse

from forge.config import load_config


def _get_forgejo_config() -> dict[str, str]:
    """Get the forgejo config section."""
    config = load_config(app_name="forge")
    return config.get("forgejo", {})


def _get_forgejo_url() -> str:
    """Get the configured Forgejo instance URL."""
    return _get_forgejo_config().get("url", "https://git.app.home.southroute.com")


def _get_package_owner() -> str:
    """Get the package registry owner from config (falls back to default_owner)."""
    cfg = _get_forgejo_config()
    return cfg.get("package_owner", "") or cfg.get("default_owner", "")


def _get_forgejo_token() -> str:
    """Resolve the Forgejo API token (same order as ForgejoClient)."""
    forgejo_cfg = _get_forgejo_config()
    token = os.environ.get("FORGE_FORGEJO__TOKEN", forgejo_cfg.get("token", ""))
    if not token:
        op_ref = forgejo_cfg.get("token_op_ref", "")
        if op_ref:
            result = subprocess.run(
                ["op", "read", op_ref],
                capture_output=True,
                text=True,
                check=False,
            )
            if result.returncode == 0:
                token = result.stdout.strip()
    return token


def _serialize_toml(data: dict[str, object]) -> str:
    """Serialize a flat TOML dict (supports strings, lists of strings, bools, ints)."""
    lines = []
    for key, value in data.items():
        if isinstance(value, list):
            if len(value) == 1:
                lines.append(f'{key} = ["{value[0]}"]')
            else:
                items = ", ".join(f'"{v}"' for v in value)
                lines.append(f"{key} = [{items}]")
        elif isinstance(value, bool):
            lines.append(f"{key} = {'true' if value else 'false'}")
        elif isinstance(value, str):
            lines.append(f'{key} = "{value}"')
        elif isinstance(value, (int, float)):
            lines.append(f"{key} = {value}")
    return "\n".join(lines) + "\n"


def _get_os_release() -> dict[str, str]:
    """Parse /etc/os-release into a dict."""
    os_release = Path("/etc/os-release")
    if not os_release.exists():
        return {}
    result = {}
    for line in os_release.read_text().splitlines():
        if "=" in line:
            key, _, value = line.partition("=")
            result[key] = value.strip('"')
    return result


def pypi(owner: str = "") -> str:
    """Add the Forgejo PyPI index to uv's global configuration."""
    if not owner:
        owner = _get_package_owner()
    if not owner:
        return "Error: no owner specified and no package_owner/default_owner in config."

    forgejo_url = _get_forgejo_url()
    pypi_url = f"{forgejo_url}/api/packages/{owner}/pypi/simple/"

    uv_config_path = Path.home() / ".config" / "uv" / "uv.toml"

    if uv_config_path.exists():
        with open(uv_config_path, "rb") as f:
            config = tomllib.load(f)
    else:
        config = {}

    urls: list[str] = list(config.get("extra-index-url", []))

    if pypi_url in urls:
        return f"Already configured: {pypi_url}"

    urls.append(pypi_url)
    config["extra-index-url"] = urls

    uv_config_path.parent.mkdir(parents=True, exist_ok=True)
    uv_config_path.write_text(_serialize_toml(config))

    return f"Added PyPI index to {uv_config_path}: {pypi_url}"


def debian(owner: str = "", codename: str = "") -> str:
    """Add the Forgejo Debian package repository. Only works on Debian-based systems."""
    os_info = _get_os_release()
    os_id = os_info.get("ID", "")
    os_id_like = os_info.get("ID_LIKE", "")

    if os_id not in ("debian", "ubuntu") and "debian" not in os_id_like:
        return f"Error: not a Debian-based system (ID={os_id})."

    if not owner:
        owner = _get_package_owner()
    if not owner:
        return "Error: no owner specified and no package_owner/default_owner in config."

    if not codename:
        codename = os_info.get("VERSION_CODENAME", "")
    if not codename:
        return "Error: could not detect version codename from /etc/os-release."

    token = _get_forgejo_token()
    if not token:
        return "Error: no Forgejo token configured. Debian registry requires authentication."

    forgejo_url = _get_forgejo_url()
    repo_url = f"{forgejo_url}/api/packages/{owner}/debian"

    # Detect system architecture to avoid 404s for unsupported architectures
    try:
        arch = subprocess.run(
            ["dpkg", "--print-architecture"],
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        arch = "amd64"

    # [trusted=yes] because Forgejo package registries are not GPG-signed
    sources_line = f"deb [arch={arch} trusted=yes] {repo_url} {codename} main"
    sources_file = Path("/etc/apt/sources.list.d/forgejo.list")
    auth_file = Path("/etc/apt/auth.conf.d/forgejo.conf")

    # Set up apt authentication via auth.conf.d (keeps token out of sources.list)
    host = urlparse(forgejo_url).hostname or ""
    auth_content = f"machine {host}\nlogin _token\npassword {token}\n"

    if sources_file.exists():
        existing = sources_file.read_text()
        if sources_line in existing:
            return f"Already configured: {sources_line}"

    # Write auth credentials
    try:
        subprocess.run(
            ["sudo", "tee", str(auth_file)],
            input=auth_content,
            text=True,
            capture_output=True,
            check=True,
        )
        subprocess.run(
            ["sudo", "chmod", "600", str(auth_file)],
            capture_output=True,
            check=True,
        )
    except subprocess.CalledProcessError as e:
        return f"Error writing {auth_file}: {e.stderr.strip()}"

    # Write sources list
    try:
        subprocess.run(
            ["sudo", "tee", str(sources_file)],
            input=sources_line + "\n",
            text=True,
            capture_output=True,
            check=True,
        )
    except subprocess.CalledProcessError as e:
        return f"Error writing {sources_file}: {e.stderr.strip()}"

    try:
        subprocess.run(
            [
                "sudo",
                "apt-get",
                "update",
                "-o",
                f"Dir::Etc::sourcelist={sources_file}",
                "-o",
                "Dir::Etc::sourceparts=-",
                "-o",
                "APT::Get::List-Cleanup=0",
            ],
            capture_output=True,
            text=True,
            check=True,
        )
    except subprocess.CalledProcessError as e:
        return f"Added {sources_file} but apt-get update failed: {e.stderr.strip()}"

    return f"Added Debian repository to {sources_file}: {sources_line}"
