"""Git remote context detection — infer owner/repo from the working directory."""

from __future__ import annotations

import os
import re
import subprocess
import sys

from rich.console import Console
from rich.prompt import IntPrompt


def get_forge_remote() -> str | None:
    """Return the remote name marked as the forge remote in .git/config.

    Looks for a remote with ``forge = true`` set via
    ``git config --get-regexp 'remote\\..*\\.forge'``.

    Returns:
        The remote name, or None if no forge remote is configured.
    """
    result = subprocess.run(
        ["git", "config", "--get-regexp", r"remote\..*\.forge"],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0 or not result.stdout.strip():
        return None

    # Output format: "remote.<name>.forge true"
    line = result.stdout.strip().splitlines()[0]
    key = line.split()[0]  # e.g. "remote.origin.forge"
    parts = key.split(".")
    if len(parts) >= 3:
        return parts[1]
    return None


def set_forge_remote(remote_name: str) -> None:
    """Mark *remote_name* as the forge remote in .git/config.

    Sets ``remote.<remote_name>.forge = true``.  Any previously marked
    forge remote is cleared first.
    """
    # Clear any existing forge remote flag
    old = get_forge_remote()
    if old:
        subprocess.run(
            ["git", "config", "--unset", f"remote.{old}.forge"],
            capture_output=True,
            check=False,
        )

    subprocess.run(
        ["git", "config", f"remote.{remote_name}.forge", "true"],
        capture_output=True,
        check=True,
    )


def _list_remotes() -> list[str]:
    """Return a list of configured git remote names."""
    result = subprocess.run(
        ["git", "remote"],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0 or not result.stdout.strip():
        return []
    return result.stdout.strip().splitlines()


def select_forge_remote() -> str:
    """Prompt the user to select which remote to use as the forge remote.

    If only one remote exists it is auto-selected.  The selection is
    persisted to ``.git/config`` so subsequent invocations skip the prompt.

    Returns:
        The selected remote name.

    Raises:
        RuntimeError: If there are no remotes or stdin is not a TTY and
            no remote can be auto-selected.
    """
    remotes = _list_remotes()
    if not remotes:
        raise RuntimeError(
            "No git remotes configured. Add a remote first with:\n"
            "  git remote add origin <url>"
        )

    if len(remotes) == 1:
        chosen = remotes[0]
        set_forge_remote(chosen)
        return chosen

    if not sys.stdin.isatty():
        # Non-interactive: fall back to origin if available, else first remote
        fallback = "origin" if "origin" in remotes else remotes[0]
        set_forge_remote(fallback)
        return fallback

    console = Console(stderr=True)
    console.print(
        "\n[bold]Select which remote to use as the Forgejo remote:[/bold]",
        highlight=False,
    )
    for i, name in enumerate(remotes, 1):
        # Show the URL alongside each remote
        url_result = subprocess.run(
            ["git", "remote", "get-url", name],
            capture_output=True,
            text=True,
            check=False,
        )
        url = url_result.stdout.strip() if url_result.returncode == 0 else ""
        console.print(f"  [bold]{i:>3}[/bold]. {name}  [dim]{url}[/dim]", highlight=False)

    default_idx = (remotes.index("origin") + 1) if "origin" in remotes else 1
    choice = IntPrompt.ask(
        "\nRemote number",
        default=default_idx,
        console=console,
    )
    if choice < 1 or choice > len(remotes):
        raise RuntimeError("Invalid selection.")

    chosen = remotes[choice - 1]
    set_forge_remote(chosen)
    console.print(
        f"[green]Using remote '[bold]{chosen}[/bold]' as forge remote.[/green]",
        highlight=False,
    )
    return chosen


def get_repo_context() -> tuple[str, str]:
    """Return (owner, repo) parsed from the forge-selected git remote URL.

    On first invocation in a repo, prompts the user to select which remote
    to use and saves the choice in ``.git/config``.

    Supports both SSH and HTTPS URL formats:
      - git@host:owner/repo.git
      - https://host/owner/repo.git
      - https://host/owner/repo

    Raises:
        RuntimeError: If not in a git repo or remote URL can't be parsed.
    """
    remote = get_forge_remote()
    if remote is None:
        remote = select_forge_remote()

    result = subprocess.run(
        ["git", "remote", "get-url", remote],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"Not in a git repository or remote '{remote}' not configured"
        )

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

    from forge.config import get_config

    config = get_config()
    return config.get("forgejo", {}).get("default_owner", "")
