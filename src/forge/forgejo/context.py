"""Git remote context detection — infer owner/repo from the working directory."""

from __future__ import annotations

import os
import re
import subprocess
import sys
from urllib.parse import urlparse

from rich.console import Console
from rich.prompt import IntPrompt


def _get_forgejo_host() -> str:
    """Return the hostname of the configured Forgejo instance.

    Resolution order: FORGE_FORGEJO__URL env var, then config file.

    Returns:
        The hostname (e.g. ``git.example.com``), or empty string if not configured.
    """
    url = os.environ.get("FORGE_FORGEJO__URL", "")
    if not url:
        from forge.config import load_config

        config = load_config()
        url = config.get("forgejo", {}).get("url", "")
    if not url:
        return ""
    return urlparse(url).hostname or ""


def _extract_host(remote_url: str) -> str:
    """Extract the hostname from a git remote URL (SSH or HTTPS).

    Returns:
        The hostname, or empty string if it cannot be parsed.
    """
    # SSH: git@host:owner/repo.git  or  ssh://git@host/owner/repo.git
    ssh_match = re.match(r"^[\w.-]+@([\w.-]+):", remote_url)
    if ssh_match:
        return ssh_match.group(1)
    # HTTPS / SSH-scheme: scheme://host/...
    parsed = urlparse(remote_url)
    return parsed.hostname or ""


def _get_remote_url(name: str) -> str:
    """Return the URL configured for git remote *name*, or empty string."""
    result = subprocess.run(
        ["git", "remote", "get-url", name],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode == 0:
        return result.stdout.strip()
    return ""


def _is_forgejo_remote(remote_name: str) -> bool:
    """Return True if *remote_name* points to the configured Forgejo instance."""
    forgejo_host = _get_forgejo_host()
    if not forgejo_host:
        return True  # can't validate without a configured URL
    url = _get_remote_url(remote_name)
    if not url:
        return False
    return _extract_host(url).lower() == forgejo_host.lower()


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


def _filter_forgejo_remotes(remotes: list[str]) -> list[str]:
    """Return only remotes whose URL points to the configured Forgejo instance."""
    forgejo_host = _get_forgejo_host()
    if not forgejo_host:
        return remotes  # can't filter without a configured URL
    return [r for r in remotes if _is_forgejo_remote(r)]


def select_forge_remote() -> str:
    """Prompt the user to select which remote to use as the forge remote.

    Only remotes pointing to the configured Forgejo instance are considered.
    If only one qualifying remote exists it is auto-selected.  The selection
    is persisted to ``.git/config`` so subsequent invocations skip the prompt.

    Returns:
        The selected remote name.

    Raises:
        RuntimeError: If there are no remotes, no remotes point to the
            Forgejo instance, or stdin is not a TTY and no remote can be
            auto-selected.
    """
    all_remotes = _list_remotes()
    if not all_remotes:
        raise RuntimeError(
            "No git remotes configured. Add a remote first with:\n  git remote add origin <url>"
        )

    remotes = _filter_forgejo_remotes(all_remotes)
    forgejo_host = _get_forgejo_host()
    if not remotes:
        non_forgejo_urls = [f"  {name} -> {_get_remote_url(name)}" for name in all_remotes]
        raise RuntimeError(
            f"No remotes point to the Forgejo instance ({forgejo_host}).\n"
            "Configured remotes:\n"
            + "\n".join(non_forgejo_urls)
            + "\n\nAdd a remote for your Forgejo instance with:\n"
            f"  git remote add forge git@{forgejo_host}:<owner>/<repo>.git"
        )

    if len(remotes) == 1:
        chosen = remotes[0]
        set_forge_remote(chosen)
        return chosen

    if not sys.stdin.isatty():
        # Non-interactive: prefer "origin" among Forgejo remotes, else first
        fallback = "origin" if "origin" in remotes else remotes[0]
        set_forge_remote(fallback)
        return fallback

    console = Console(stderr=True)
    console.print(
        "\n[bold]Select which remote to use as the Forgejo remote:[/bold]",
        highlight=False,
    )
    for i, name in enumerate(remotes, 1):
        url = _get_remote_url(name)
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
    to use and saves the choice in ``.git/config``.  If the saved remote no
    longer points to the configured Forgejo instance, the selection is
    cleared and the user is prompted again.

    Supports both SSH and HTTPS URL formats:
      - git@host:owner/repo.git
      - https://host/owner/repo.git
      - https://host/owner/repo

    Raises:
        RuntimeError: If not in a git repo or remote URL can't be parsed.
    """
    remote = get_forge_remote()
    if remote is not None and not _is_forgejo_remote(remote):
        # Saved remote no longer points to Forgejo — clear and re-select
        console = Console(stderr=True)
        url = _get_remote_url(remote)
        console.print(
            f"[yellow]Warning:[/yellow] saved forge remote '{remote}' "
            f"({url}) does not point to the Forgejo instance "
            f"({_get_forgejo_host()}). Re-selecting.",
            highlight=False,
        )
        subprocess.run(
            ["git", "config", "--unset", f"remote.{remote}.forge"],
            capture_output=True,
            check=False,
        )
        remote = None
    if remote is None:
        remote = select_forge_remote()

    result = subprocess.run(
        ["git", "remote", "get-url", remote],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(f"Not in a git repository or remote '{remote}' not configured")

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

    from forge.config import load_config

    config = load_config()
    return config.get("forgejo", {}).get("default_owner", "")
