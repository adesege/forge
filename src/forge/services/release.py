"""Release service — manage Forgejo releases."""

from __future__ import annotations

from typing import Any

from click_clop.service import Service

from forge.forgejo import get_client
from forge.forgejo.context import get_repo_context
from forge.forgejo.formatting import format_release, format_table


class ReleaseService(Service):
    """Forgejo release operations."""

    name = "release"
    description = "Manage releases"

    def list(
        self, owner: str = "", repo: str = "", limit: int = 30, page: int = 1
    ) -> str:
        """List releases."""
        if not owner or not repo:
            owner, repo = get_repo_context()
        client = get_client()
        data = client.get(
            f"/repos/{owner}/{repo}/releases",
            params={"limit": limit, "page": page},
        )
        if not data:
            return "No releases found."
        return format_table(
            data,
            [
                ("tag_name", "Tag"),
                ("name", "Title"),
                ("author", "Author"),
                ("published_at", "Published"),
            ],
            title=f"Releases — {owner}/{repo}",
        )

    def view(self, tag: str = "", owner: str = "", repo: str = "") -> str:
        """View release details by tag."""
        if not owner or not repo:
            owner, repo = get_repo_context()
        if not tag:
            return "Error: --tag is required."
        client = get_client()
        data = client.get(f"/repos/{owner}/{repo}/releases/tags/{tag}")
        return format_release(data)

    def create(
        self,
        tag: str = "",
        title: str = "",
        body: str = "",
        draft: bool = False,
        prerelease: bool = False,
        owner: str = "",
        repo: str = "",
    ) -> str:
        """Create a release."""
        if not owner or not repo:
            owner, repo = get_repo_context()
        if not tag:
            return "Error: --tag is required."
        client = get_client()
        payload: dict[str, Any] = {
            "tag_name": tag,
            "name": title or tag,
            "draft": draft,
            "prerelease": prerelease,
        }
        if body:
            payload["body"] = body
        data = client.post(f"/repos/{owner}/{repo}/releases", json=payload)
        return f"Created release: {data.get('name', tag)}\n{data.get('html_url', '')}"

    def delete(self, tag: str = "", owner: str = "", repo: str = "") -> str:
        """Delete a release by tag."""
        if not owner or not repo:
            owner, repo = get_repo_context()
        if not tag:
            return "Error: --tag is required."
        client = get_client()
        # Get release ID by tag, then delete
        release = client.get(f"/repos/{owner}/{repo}/releases/tags/{tag}")
        client.delete(f"/repos/{owner}/{repo}/releases/{release['id']}")
        return f"Deleted release: {tag}"

    def edit(
        self,
        tag: str = "",
        title: str = "",
        body: str = "",
        draft: bool = False,
        prerelease: bool = False,
        owner: str = "",
        repo: str = "",
    ) -> str:
        """Edit a release."""
        if not owner or not repo:
            owner, repo = get_repo_context()
        if not tag:
            return "Error: --tag is required."
        client = get_client()
        release = client.get(f"/repos/{owner}/{repo}/releases/tags/{tag}")
        payload: dict[str, Any] = {
            "draft": draft,
            "prerelease": prerelease,
        }
        if title:
            payload["name"] = title
        if body:
            payload["body"] = body
        data = client.patch(
            f"/repos/{owner}/{repo}/releases/{release['id']}", json=payload
        )
        return f"Updated release: {data.get('name', tag)}"


_service = ReleaseService()
