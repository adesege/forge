"""PR service — manage Forgejo pull requests."""

from __future__ import annotations

import json
import re
from typing import Any

from forge.forgejo import get_client
from forge.forgejo.context import get_default_owner, get_repo_context
from forge.forgejo.exceptions import ForgejoNotFoundError
from forge.forgejo.formatting import format_checks, format_pr, format_table


def _list_prs_for_owner(
    owner: str,
    state: str = "open",
    limit: int = 30,
) -> str:
    """List pull requests across all repos for an owner."""
    client = get_client()
    repos = client.get(f"/users/{owner}/repos", params={"limit": 50})
    if not repos:
        return f"No repositories found for {owner}."
    all_prs: list[dict[str, Any]] = []
    for r in repos:
        repo_name = r.get("name", "")
        if not repo_name:
            continue
        try:
            prs = client.get(
                f"/repos/{owner}/{repo_name}/pulls",
                params={"state": state, "limit": limit},
            )
        except ForgejoNotFoundError:
            continue
        if prs:
            for p in prs:
                p["_repo"] = repo_name
            all_prs.extend(prs)
    if not all_prs:
        return f"No pull requests found for {owner} ({state})."
    all_prs.sort(key=lambda p: p.get("updated_at", ""), reverse=True)
    all_prs = all_prs[:limit]
    return format_table(
        all_prs,
        [
            ("_repo", "Repo"),
            ("number", "#"),
            ("title", "Title"),
            ("state", "State"),
            ("user", "Author"),
        ],
        title=f"Pull Requests — {owner} ({state})",
    )


def list_prs(
    owner: str = "",
    repo: str = "",
    state: str = "open",
    limit: int = 30,
    page: int = 1,
) -> str:
    """List pull requests.

    When owner is given without repo, lists PRs across all repos for that owner.
    When neither is given, owner falls back to default_owner from config; if a
    repo still can't be determined the current git context is used.
    """
    if not owner:
        owner = get_default_owner()
    if owner and not repo:
        return _list_prs_for_owner(owner, state=state, limit=limit)
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


def _parse_comment_id(raw: str) -> tuple[int, str, str] | None:
    """Parse a comment ID from a raw string.

    Accepts either a bare integer or a Forgejo Message-ID format:
      ``<owner/repo/pulls/PR/comment/COMMENT_ID@host>``

    Returns ``(comment_id, owner, repo)`` or ``None`` if unparseable.
    The owner/repo may be empty strings if only a bare integer was given.
    """
    raw = raw.strip().strip("<>")
    # Try bare integer first
    if raw.isdigit():
        return int(raw), "", ""
    # Try Forgejo Message-ID format: owner/repo/pulls/N/comment/ID@host
    m = re.match(r"([^/]+/[^/]+)/(?:pulls|issues)/\d+/comment/(\d+)@", raw)
    if m:
        parts = m.group(1).split("/", 1)
        return int(m.group(2)), parts[0], parts[1]
    return None


def react(
    comment_id: str = "",
    reaction: str = "+1",
    owner: str = "",
    repo: str = "",
) -> str:
    """Add a reaction to an issue/PR comment.

    The ``comment_id`` can be a bare integer or a Forgejo Message-ID string
    like ``<owner/repo/pulls/1/comment/42@host>``.  When a Message-ID is
    given, the owner and repo are extracted automatically.

    Supported reactions: +1, -1, laugh, hooray, confused, heart, rocket, eyes.
    """
    if not comment_id:
        return "Error: --comment-id is required."
    parsed = _parse_comment_id(comment_id)
    if parsed is None:
        return f"Error: cannot parse comment ID from: {comment_id}"
    cid, parsed_owner, parsed_repo = parsed
    owner = owner or parsed_owner
    repo = repo or parsed_repo
    if not owner or not repo:
        owner, repo = get_repo_context()
    client = get_client()
    data = client.post(
        f"/repos/{owner}/{repo}/issues/comments/{cid}/reactions",
        json={"content": reaction},
    )
    return f"Reacted {data.get('content', reaction)} to comment {cid}"


def _scrape_steps(html: str) -> list[dict[str, Any]]:
    """Extract step details from Forgejo action run HTML.

    The web UI embeds job data in a ``data-initial-post-response`` attribute
    as a JSON object.  We parse that to get step names, statuses, and log
    lines.
    """
    match = re.search(r'data-initial-post-response="([^"]*)"', html)
    if not match:
        return []
    raw = match.group(1).replace("&quot;", '"').replace("&amp;", "&")
    try:
        data = json.loads(raw)
    except json.JSONDecodeError, TypeError:
        return []
    steps = data.get("state", {}).get("run", {}).get("steps", [])
    result: list[dict[str, Any]] = []
    for step in steps:
        entry: dict[str, Any] = {
            "name": step.get("name", ""),
            "status": step.get("status", "unknown"),
            "duration": step.get("duration", ""),
        }
        log_lines = step.get("logLines", [])
        if log_lines:
            entry["log"] = "\n".join(
                line.get("message", "") for line in log_lines if isinstance(line, dict)
            )
        result.append(entry)
    return result


def checks(number: int = 0, owner: str = "", repo: str = "") -> str:
    """View CI check status and step details for a pull request."""
    if not owner or not repo:
        owner, repo = get_repo_context()
    if not number:
        return "Error: --number is required."
    client = get_client()

    # Get PR to find head SHA
    pr_data = client.get(f"/repos/{owner}/{repo}/pulls/{number}")
    head_sha = pr_data.get("head", {}).get("sha", "")
    if not head_sha:
        return f"PR #{number} has no head commit SHA."

    # Get commit statuses
    statuses = client.get(f"/repos/{owner}/{repo}/statuses/{head_sha}")
    if not isinstance(statuses, list):
        statuses = []

    # Try to get action runs for this repo to find runs matching the SHA
    runs: list[dict[str, Any]] = []
    try:
        run_data = client.get(
            f"/repos/{owner}/{repo}/actions/tasks",
            params={"limit": 20},
        )
        if isinstance(run_data, dict):
            for wf_run in run_data.get("workflow_runs", []):
                if wf_run.get("head_sha") == head_sha:
                    runs.append(wf_run)
    except Exception:
        pass

    # Scrape step details from the web UI for each run
    run_details: list[dict[str, Any]] = []
    for status in statuses:
        target_url = status.get("target_url", "")
        detail: dict[str, Any] = {
            "context": status.get("context", ""),
            "state": status.get("status", ""),
            "description": status.get("description", ""),
            "target_url": target_url,
            "steps": [],
        }
        if target_url:
            # Extract the run path from the target URL
            # e.g. https://host/owner/repo/actions/runs/123
            path_match = re.search(r"(/[^/]+/[^/]+/actions/runs/\d+)", target_url)
            if path_match:
                try:
                    html = client.get_html(path_match.group(1))
                    detail["steps"] = _scrape_steps(html)
                except Exception:
                    pass
        run_details.append(detail)

    return format_checks(number, head_sha, run_details)
