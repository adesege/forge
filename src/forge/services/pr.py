"""PR service — manage Forgejo pull requests."""

from __future__ import annotations

from typing import Any

from forge.forgejo import get_client
from forge.forgejo.context import get_repo_context
from forge.forgejo.formatting import format_pr, format_table


def list_prs(
    owner: str = "",
    repo: str = "",
    state: str = "open",
    limit: int = 30,
    page: int = 1,
) -> str:
    """List pull requests."""
    if not owner or not repo:
        owner, repo = get_repo_context()
    client = get_client()
    params: dict[str, Any] = {"state": state, "limit": limit, "page": page}
    data = client.get(f"/repos/{owner}/{repo}/pulls", params=params)
    if not data:
        return "No pull requests found."
    return format_table(
        data,
        [
            ("number", "#"),
            ("title", "Title"),
            ("state", "State"),
            ("user", "Author"),
        ],
        title=f"Pull Requests — {owner}/{repo} ({state})",
    )


def view(number: int = 0, owner: str = "", repo: str = "") -> str:
    """View pull request details."""
    if not owner or not repo:
        owner, repo = get_repo_context()
    if not number:
        return "Error: --number is required."
    client = get_client()
    data = client.get(f"/repos/{owner}/{repo}/pulls/{number}")
    return format_pr(data)


def create(
    title: str = "",
    body: str = "",
    head: str = "",
    base: str = "main",
    owner: str = "",
    repo: str = "",
) -> str:
    """Create a pull request."""
    if not owner or not repo:
        owner, repo = get_repo_context()
    if not title:
        return "Error: --title is required."
    if not head:
        return "Error: --head is required (source branch)."
    client = get_client()
    payload: dict[str, str] = {
        "title": title,
        "head": head,
        "base": base,
    }
    if body:
        payload["body"] = body
    data = client.post(f"/repos/{owner}/{repo}/pulls", json=payload)
    return f"Created PR #{data['number']}: {data['title']}\n{data.get('html_url', '')}"


def merge(
    number: int = 0,
    method: str = "merge",
    owner: str = "",
    repo: str = "",
) -> str:
    """Merge a pull request. Method: merge, rebase, or squash."""
    if not owner or not repo:
        owner, repo = get_repo_context()
    if not number:
        return "Error: --number is required."
    client = get_client()
    client.post(
        f"/repos/{owner}/{repo}/pulls/{number}/merge",
        json={"Do": method},
    )
    return f"Merged PR #{number} via {method}"


def close(number: int = 0, owner: str = "", repo: str = "") -> str:
    """Close a pull request."""
    if not owner or not repo:
        owner, repo = get_repo_context()
    if not number:
        return "Error: --number is required."
    client = get_client()
    client.patch(f"/repos/{owner}/{repo}/pulls/{number}", json={"state": "closed"})
    return f"Closed PR #{number}"


def reopen(number: int = 0, owner: str = "", repo: str = "") -> str:
    """Reopen a closed pull request."""
    if not owner or not repo:
        owner, repo = get_repo_context()
    if not number:
        return "Error: --number is required."
    client = get_client()
    client.patch(f"/repos/{owner}/{repo}/pulls/{number}", json={"state": "open"})
    return f"Reopened PR #{number}"


def diff(number: int = 0, owner: str = "", repo: str = "") -> str:
    """View the diff of a pull request."""
    if not owner or not repo:
        owner, repo = get_repo_context()
    if not number:
        return "Error: --number is required."
    client = get_client()
    return client.get_raw(f"/repos/{owner}/{repo}/pulls/{number}.diff")


def review(
    number: int = 0,
    body: str = "",
    event: str = "COMMENT",
    owner: str = "",
    repo: str = "",
) -> str:
    """Submit a review on a pull request.

    Event types: APPROVE, REQUEST_CHANGES, COMMENT.
    """
    if not owner or not repo:
        owner, repo = get_repo_context()
    if not number:
        return "Error: --number is required."
    client = get_client()
    payload: dict[str, str] = {"event": event}
    if body:
        payload["body"] = body
    data = client.post(f"/repos/{owner}/{repo}/pulls/{number}/reviews", json=payload)
    return f"Submitted {event} review on PR #{number} (review #{data.get('id', '?')})"
