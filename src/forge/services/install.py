"""Install service — configure package repositories for forge."""

from __future__ import annotations

import subprocess
import tomllib
from pathlib import Path

from click_clop.service import Service

from forge.config import get_config


def _get_forgejo_url() -> str:
    """Get the configured Forgejo instance URL."""
    config = get_config()
    return config.get("forgejo", {}).get("url", "https://git.app.home.southroute.com")


def _get_default_owner() -> str:
    """Get the default package owner from config."""
    config = get_config()
    return config.get("forgejo", {}).get("default_owner", "")


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


class InstallService(Service):
    """Configure package repositories for installing forge."""

    name = "install"
    description = "Configure package repositories"

    def pypi(self, owner: str = "") -> str:
        """Add the Forgejo PyPI index to uv's global configuration."""
        if not owner:
            owner = _get_default_owner()
        if not owner:
            return "Error: no owner specified and no default_owner in config."

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

    def debian(self, owner: str = "", codename: str = "") -> str:
        """Add the Forgejo Debian package repository. Only works on Debian-based systems."""
        os_info = _get_os_release()
        os_id = os_info.get("ID", "")
        os_id_like = os_info.get("ID_LIKE", "")

        if os_id not in ("debian", "ubuntu") and "debian" not in os_id_like:
            return f"Error: not a Debian-based system (ID={os_id})."

        if not owner:
            owner = _get_default_owner()
        if not owner:
            return "Error: no owner specified and no default_owner in config."

        if not codename:
            codename = os_info.get("VERSION_CODENAME", "")
        if not codename:
            return "Error: could not detect version codename from /etc/os-release."

        forgejo_url = _get_forgejo_url()
        repo_url = f"{forgejo_url}/api/packages/{owner}/debian"
        sources_line = f"deb {repo_url} {codename} main"
        sources_file = Path("/etc/apt/sources.list.d/forgejo.list")

        if sources_file.exists():
            existing = sources_file.read_text()
            if sources_line in existing:
                return f"Already configured: {sources_line}"

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
                ["sudo", "apt-get", "update", "-o", f"Dir::Etc::sourcelist={sources_file}",
                 "-o", "Dir::Etc::sourceparts=-", "-o", "APT::Get::List-Cleanup=0"],
                capture_output=True,
                text=True,
                check=True,
            )
        except subprocess.CalledProcessError as e:
            return f"Added {sources_file} but apt-get update failed: {e.stderr.strip()}"

        return f"Added Debian repository to {sources_file}: {sources_line}"


_service = InstallService()
