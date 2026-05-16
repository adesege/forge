"""Actions service — CI/CD run status and logs."""

from __future__ import annotations

from typing import Any

from forge.forgejo import get_client
from forge.forgejo.context import get_repo_context
from forge.forgejo.formatting import format_run_detail, format_table


def list_runs(
    owner: str = "",
    repo: str = "",
    status: str = "",
    event: str = "",
    limit: int = 30,
    page: int = 1,
) -> str:
    """List action runs for a repository."""
    if not owner or not repo:
        owner, repo = get_repo_context()
    client = get_client()
    params: dict[str, Any] = {"limit": limit, "page": page}
    if status:
        params["status"] = status
    if event:
        params["event"] = event
    data = client.get(f"/repos/{owner}/{repo}/actions/runs", params=params)
    runs = data.get("workflow_runs", []) if isinstance(data, dict) else data
    if not runs:
        return "No action runs found."
    return format_table(
        runs,
        [
            ("index_in_repo", "#"),
            ("status", "Status"),
            ("title", "Title"),
            ("event", "Event"),
            ("commit_sha", "SHA"),
            ("started", "Started"),
        ],
        title=f"Action Runs — {owner}/{repo}",
    )


def view_run(
    run_id: int = 0,
    owner: str = "",
    repo: str = "",
) -> str:
    """View details of an action run."""
    if not owner or not repo:
        owner, repo = get_repo_context()
    if not run_id:
        return "Error: --run-id is required."
    client = get_client()
    data = client.get(f"/repos/{owner}/{repo}/actions/runs/{run_id}")
    return format_run_detail(data)


def log(
    run_id: int = 0,
    job: int = 0,
    owner: str = "",
    repo: str = "",
) -> str:
    """Get log output for a CI run job.

    Uses the web UI logs endpoint since Forgejo does not expose a log
    endpoint in /api/v1.
    """
    if not owner or not repo:
        owner, repo = get_repo_context()
    if not run_id:
        return "Error: --run-id is required."

    client = get_client()

    content = client.get_web_text(
        f"/{owner}/{repo}/actions/runs/{run_id}/jobs/{job}/attempt/1/logs",
    )

    if not content:
        return "No log data returned."

    return content


def commit_status(
    ref: str = "",
    owner: str = "",
    repo: str = "",
) -> str:
    """Get commit statuses (CI check results) for a ref."""
    if not owner or not repo:
        owner, repo = get_repo_context()
    if not ref:
        return "Error: --ref is required (branch, tag, or commit SHA)."
    client = get_client()
    data = client.get(f"/repos/{owner}/{repo}/commits/{ref}/statuses")
    if not data:
        return f"No statuses found for {ref}."
    return format_table(
        data,
        [
            ("context", "Context"),
            ("status", "Status"),
            ("description", "Description"),
            ("target_url", "URL"),
        ],
        title=f"Commit Statuses — {ref[:12]}",
    )
