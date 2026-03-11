"""Git remote context detection — infer owner/repo from the working directory."""

from __future__ import annotations

import os
import re
import subprocess


def get_repo_context() -> tuple[str, str]:
    """Return (owner, repo) parsed from the git remote 'origin' URL.

    Supports both SSH and HTTPS URL formats:
      - git@host:owner/repo.git
      - https://host/owner/repo.git
      - https://host/owner/repo

    Raises:
        RuntimeError: If not in a git repo or remote URL can't be parsed.
    """
    result = subprocess.run(
        ["git", "remote", "get-url", "origin"],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError("Not in a git repository or no 'origin' remote configured")

    url = result.stdout.strip()
    return parse_remote_url(url)


def parse_remote_url(url: str) -> tuple[str, str]:
    """Parse a git remote URL into (owner, repo).

    Raises:
        ValueError: If the URL format is not recognized.
    """
    # SSH: git@host:owner/repo.git
    ssh_match = re.match(r"^[\w.-]+@[\w.-]+:([\w._-]+)/([\w._-]+?)(?:\.git)?$", url)
    if ssh_match:
        return ssh_match.group(1), ssh_match.group(2)

    # HTTPS: https://host/owner/repo.git
    https_match = re.match(r"^https?://[\w.-]+(?::\d+)?/([\w._-]+)/([\w._-]+?)(?:\.git)?$", url)
    if https_match:
        return https_match.group(1), https_match.group(2)

    raise ValueError(f"Cannot parse git remote URL: {url}")


def get_default_owner() -> str:
    """Return the default owner from config, or empty string if not set.

    Resolution order:
    1. FORGE_FORGEJO__DEFAULT_OWNER env var
    2. config["forgejo"]["default_owner"]
    """
    env_val = os.environ.get("FORGE_FORGEJO__DEFAULT_OWNER", "")
    if env_val:
        return env_val

    from click_clop.config import load_config

    config = load_config(None, env_prefix="FORGE_")
    return config.get("forgejo", {}).get("default_owner", "")
