"""Org service — manage Forgejo organizations."""

from __future__ import annotations

from forge.forgejo import get_client
from forge.forgejo.formatting import format_org, format_table


def list_orgs() -> str:
    """List organizations the authenticated user belongs to."""
    client = get_client()
    data = client.get("/user/orgs")
    if not data:
        return "No organizations found."
    return format_table(
        data,
        [
            ("username", "Organization"),
            ("description", "Description"),
            ("visibility", "Visibility"),
        ],
        title="Organizations",
    )


def view(org: str = "") -> str:
    """View organization details."""
    if not org:
        return "Error: --org is required."
    client = get_client()
    data = client.get(f"/orgs/{org}")
    return format_org(data)


def repos(org: str = "", limit: int = 30, page: int = 1) -> str:
    """List repositories in an organization."""
    if not org:
        return "Error: --org is required."
    client = get_client()
    data = client.get(f"/orgs/{org}/repos", params={"limit": limit, "page": page})
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
        title=f"Repositories — {org}",
    )


def members(org: str = "", limit: int = 30, page: int = 1) -> str:
    """List members of an organization."""
    if not org:
        return "Error: --org is required."
    client = get_client()
    data = client.get(f"/orgs/{org}/members", params={"limit": limit, "page": page})
    if not data:
        return "No members found."
    return format_table(
        data,
        [
            ("login", "Username"),
            ("full_name", "Name"),
            ("email", "Email"),
        ],
        title=f"Members — {org}",
    )
