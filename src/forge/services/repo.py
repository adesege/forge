"""Repo service — manage Forgejo repositories."""

from __future__ import annotations

import os
import subprocess
import sys

from click_clop.service import Service
from rich.console import Console
from rich.prompt import IntPrompt

from forge.forgejo import get_client
from forge.forgejo.context import get_default_owner, get_repo_context
from forge.forgejo.formatting import format_repo, format_table


class RepoService(Service):
    """Forgejo repository operations."""

    name = "repo"
    description = "Manage repositories"

    def list(self, owner: str = "", limit: int = 30, page: int = 1) -> str:
        """List repositories for a user/org or the authenticated user."""
        if not owner:
            owner = get_default_owner()
        client = get_client()
        params: dict[str, int] = {"limit": limit, "page": page}
        if owner:
            data = client.get(f"/users/{owner}/repos", params=params)
        else:
            data = client.get("/user/repos", params=params)
        if not data:
            return "No repositories found."
        return format_table(
            data,
            [
                ("full_name", "Repository"),
                ("description", "Description"),
                ("stars_count", "Stars"),
                ("language", "Language"),
            ],
            title="Repositories",
        )

    def view(self, owner: str = "", repo: str = "") -> str:
        """View repository details. Infers owner/repo from git remote if omitted."""
        if not owner or not repo:
            owner, repo = get_repo_context()
        client = get_client()
        data = client.get(f"/repos/{owner}/{repo}")
        return format_repo(data)

    def create(
        self,
        name: str = "",
        description: str = "",
        private: bool = False,
        org: str = "",
    ) -> str:
        """Create a new repository.

        Defaults name to current directory basename.
        Sets git origin to the new repo.
        """
        if not name:
            name = os.path.basename(os.getcwd())
        if not name:
            return "Error: could not determine repository name."
        if not org:
            org = get_default_owner()
        client = get_client()
        body = {
            "name": name,
            "description": description,
            "private": private,
        }
        if org:
            data = client.post(f"/orgs/{org}/repos", json=body)
        else:
            data = client.post("/user/repos", json=body)

        origin_url = data.get("ssh_url", data.get("clone_url", ""))
        if origin_url:
            self._set_origin(origin_url)

        return f"Created repository: {data['full_name']}\n{data.get('html_url', '')}"

    @staticmethod
    def _set_origin(url: str) -> None:
        """Set or update the git remote 'origin' to the given URL."""
        result = subprocess.run(
            ["git", "remote", "get-url", "origin"],
            capture_output=True,
            check=False,
        )
        if result.returncode == 0:
            subprocess.run(
                ["git", "remote", "set-url", "origin", url],
                capture_output=True,
                check=True,
            )
        else:
            subprocess.run(
                ["git", "remote", "add", "origin", url],
                capture_output=True,
                check=True,
            )


    def clone(self, name: str = "", owner: str = "", directory: str = "") -> str:
        """Clone a repository. Shows an interactive selector if name is omitted."""
        if not owner:
            owner = get_default_owner()
        client = get_client()

        if not name:
            # Fetch repos for selection
            params: dict[str, int] = {"limit": 50}
            if owner:
                repos = client.get(f"/users/{owner}/repos", params=params)
            else:
                repos = client.get("/user/repos", params=params)

            if not repos:
                return "No repositories found."

            if not sys.stdin.isatty():
                return format_table(
                    repos,
                    [
                        ("full_name", "Repository"),
                        ("description", "Description"),
                    ],
                    title="Repositories (pass --name to clone)",
                )

            console = Console(stderr=True)
            for i, r in enumerate(repos, 1):
                desc = r.get("description", "")
                label = f"  [bold]{i:>3}[/bold]. {r['full_name']}"
                if desc:
                    label += f"  [dim]— {desc}[/dim]"
                console.print(label, highlight=False)

            choice = IntPrompt.ask("\nSelect repository", default=1, console=console)
            if choice < 1 or choice > len(repos):
                return "Invalid selection."

            selected = repos[choice - 1]
            name = selected["name"]
            owner = selected.get("owner", {}).get("login", owner)

        data = client.get(f"/repos/{owner}/{name}")
        clone_url = data.get("ssh_url", data.get("clone_url", ""))
        if not clone_url:
            return "Error: could not determine clone URL."

        target = directory or name
        result = subprocess.run(
            ["git", "clone", clone_url, target],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            return f"Error cloning: {result.stderr.strip()}"
        return f"Cloned {data['full_name']} into {target}/"

    def fork(self, owner: str = "", repo: str = "", org: str = "") -> str:
        """Fork a repository. Uses default_owner from config as org if not specified."""
        if not owner or not repo:
            owner, repo = get_repo_context()
        if not org:
            org = get_default_owner()
        client = get_client()
        body: dict[str, str] = {}
        if org:
            body["organization"] = org
        data = client.post(f"/repos/{owner}/{repo}/forks", json=body)
        return f"Forked to: {data['full_name']}\n{data.get('html_url', '')}"

    def delete(self, owner: str = "", repo: str = "") -> str:
        """Delete a repository."""
        if not owner or not repo:
            owner, repo = get_repo_context()
        client = get_client()
        client.delete(f"/repos/{owner}/{repo}")
        return f"Deleted repository: {owner}/{repo}"

    def search(self, query: str = "", limit: int = 30) -> str:
        """Search repositories."""
        if not query:
            return "Error: --query is required."
        client = get_client()
        data = client.get("/repos/search", params={"q": query, "limit": limit})
        repos = data.get("data", []) if isinstance(data, dict) else data
        if not repos:
            return "No repositories found."
        return format_table(
            repos,
            [
                ("full_name", "Repository"),
                ("description", "Description"),
                ("stars_count", "Stars"),
                ("language", "Language"),
            ],
            title=f'Search results for "{query}"',
        )


_service = RepoService()
