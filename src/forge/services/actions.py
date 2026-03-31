"""Actions service — CI/CD run status and logs."""

from __future__ import annotations

from typing import Any

from forge.forgejo import get_client
from forge.forgejo.context import get_repo_context
from forge.forgejo.formatting import format_run, format_run_detail, format_table


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
    step: int = 0,
    owner: str = "",
    repo: str = "",
) -> str:
    """Get log output for a CI run step.

    Uses the internal web UI endpoint (not the REST API) since Forgejo
    does not expose a log endpoint in /api/v1.
    """
    if not owner or not repo:
        owner, repo = get_repo_context()
    if not run_id:
        return "Error: --run-id is required."

    client = get_client()

    # Build logCursors: mark the requested step as expanded
    num_steps = max(step + 1, 10)
    log_cursors = [{"step": i, "cursor": None, "expanded": i == step} for i in range(num_steps)]

    data = client.post_web_authenticated(
        f"/{owner}/{repo}/actions/runs/{run_id}/jobs/{job}",
        json={"logCursors": log_cursors},
    )

    if not data:
        return "No log data returned."

    logs = data.get("logs", {})
    if not logs:
        # Try alternate response shape
        state = data.get("state", {})
        if state and state.get("steps"):
            return format_run(data)
        return "No log data returned."

    return _format_logs(logs, step)


def _format_logs(logs: dict[str, Any], step: int) -> str:
    """Extract and format log lines from the web UI response."""
    step_key = str(step)
    step_data = logs.get(step_key, logs.get(f"step{step}", {}))
    if not step_data:
        # Return all available logs
        lines: list[str] = []
        for key in sorted(logs.keys(), key=lambda k: int(k) if k.isdigit() else 0):
            entry = logs[key]
            if isinstance(entry, dict):
                cursor_data = entry.get("lines", [])
                if cursor_data:
                    for line in cursor_data:
                        msg = line.get("message", "") if isinstance(line, dict) else str(line)
                        lines.append(msg)
            elif isinstance(entry, list):
                for line in entry:
                    msg = line.get("message", "") if isinstance(line, dict) else str(line)
                    lines.append(msg)
        return "\n".join(lines) if lines else "No log lines found."

    # Single step
    if isinstance(step_data, dict):
        cursor_data = step_data.get("lines", [])
    elif isinstance(step_data, list):
        cursor_data = step_data
    else:
        return str(step_data)

    lines = []
    for line in cursor_data:
        msg = line.get("message", "") if isinstance(line, dict) else str(line)
        lines.append(msg)
    return "\n".join(lines) if lines else "No log lines for this step."


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
