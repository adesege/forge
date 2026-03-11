"""Repo service — manage Forgejo repositories."""

from __future__ import annotations

from click_clop.service import Service

from forge.forgejo import get_client
from forge.forgejo.context import get_repo_context
from forge.forgejo.formatting import format_repo, format_table


class RepoService(Service):
    """Forgejo repository operations."""

    name = "repo"
    description = "Manage repositories"

    def list(self, owner: str = "", limit: int = 30, page: int = 1) -> str:
        """List repositories for a user or the authenticated user."""
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
        """Create a new repository."""
        if not name:
            return "Error: --name is required."
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
        return f"Created repository: {data['full_name']}\n{data.get('html_url', '')}"

    def fork(self, owner: str = "", repo: str = "", org: str = "") -> str:
        """Fork a repository."""
        if not owner or not repo:
            owner, repo = get_repo_context()
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
