"""Issue service — manage Forgejo issues."""

from __future__ import annotations

from typing import Any

from forge.forgejo import get_client
from forge.forgejo.context import get_repo_context
from forge.forgejo.formatting import format_issue, format_table


def list_issues(
    owner: str = "",
    repo: str = "",
    state: str = "open",
    labels: str = "",
    milestone: str = "",
    limit: int = 30,
    page: int = 1,
) -> str:
    """List issues. Labels are comma-separated."""
    if not owner or not repo:
        owner, repo = get_repo_context()
    client = get_client()
    params: dict[str, Any] = {
        "state": state,
        "type": "issues",
        "limit": limit,
        "page": page,
    }
    if labels:
        params["labels"] = labels
    if milestone:
        params["milestone"] = milestone
    data = client.get(f"/repos/{owner}/{repo}/issues", params=params)
    if not data:
        return "No issues found."
    return format_table(
        data,
        [
            ("number", "#"),
            ("title", "Title"),
            ("state", "State"),
            ("user", "Author"),
        ],
        title=f"Issues — {owner}/{repo} ({state})",
    )


def view(number: int = 0, owner: str = "", repo: str = "") -> str:
    """View issue details."""
    if not owner or not repo:
        owner, repo = get_repo_context()
    if not number:
        return "Error: --number is required."
    client = get_client()
    data = client.get(f"/repos/{owner}/{repo}/issues/{number}")
    return format_issue(data)


def create(
    title: str = "",
    body: str = "",
    labels: str = "",
    assignees: str = "",
    milestone: int = 0,
    owner: str = "",
    repo: str = "",
) -> str:
    """Create an issue. Labels and assignees are comma-separated."""
    if not owner or not repo:
        owner, repo = get_repo_context()
    if not title:
        return "Error: --title is required."
    client = get_client()
    payload: dict[str, Any] = {"title": title}
    if body:
        payload["body"] = body
    if labels:
        label_ids = _resolve_labels(client, owner, repo, labels)
        if label_ids:
            payload["labels"] = label_ids
    if assignees:
        payload["assignees"] = [a.strip() for a in assignees.split(",")]
    if milestone:
        payload["milestone"] = milestone
    data = client.post(f"/repos/{owner}/{repo}/issues", json=payload)
    return f"Created issue #{data['number']}: {data['title']}\n{data.get('html_url', '')}"


def close(number: int = 0, owner: str = "", repo: str = "") -> str:
    """Close an issue."""
    if not owner or not repo:
        owner, repo = get_repo_context()
    if not number:
        return "Error: --number is required."
    client = get_client()
    client.patch(f"/repos/{owner}/{repo}/issues/{number}", json={"state": "closed"})
    return f"Closed issue #{number}"


def reopen(number: int = 0, owner: str = "", repo: str = "") -> str:
    """Reopen a closed issue."""
    if not owner or not repo:
        owner, repo = get_repo_context()
    if not number:
        return "Error: --number is required."
    client = get_client()
    client.patch(f"/repos/{owner}/{repo}/issues/{number}", json={"state": "open"})
    return f"Reopened issue #{number}"


def comment(number: int = 0, body: str = "", owner: str = "", repo: str = "") -> str:
    """Add a comment to an issue."""
    if not owner or not repo:
        owner, repo = get_repo_context()
    if not number:
        return "Error: --number is required."
    if not body:
        return "Error: --body is required."
    client = get_client()
    data = client.post(
        f"/repos/{owner}/{repo}/issues/{number}/comments",
        json={"body": body},
    )
    return f"Added comment to issue #{number}\n{data.get('html_url', '')}"


def edit(
    number: int = 0,
    title: str = "",
    body: str = "",
    owner: str = "",
    repo: str = "",
) -> str:
    """Edit an issue's title and/or body."""
    if not owner or not repo:
        owner, repo = get_repo_context()
    if not number:
        return "Error: --number is required."
    payload: dict[str, str] = {}
    if title:
        payload["title"] = title
    if body:
        payload["body"] = body
    if not payload:
        return "Error: provide --title and/or --body to edit."
    client = get_client()
    data = client.patch(f"/repos/{owner}/{repo}/issues/{number}", json=payload)
    return f"Updated issue #{data['number']}: {data['title']}"


def _resolve_labels(client: Any, owner: str, repo: str, labels_csv: str) -> list[int]:
    """Resolve comma-separated label names to IDs."""
    names = [n.strip() for n in labels_csv.split(",") if n.strip()]
    if not names:
        return []
    all_labels = client.get(f"/repos/{owner}/{repo}/labels")
    label_map: dict[str, int] = {lb["name"]: lb["id"] for lb in all_labels}
    return [label_map[n] for n in names if n in label_map]
