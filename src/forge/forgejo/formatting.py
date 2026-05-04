"""Rich-based output formatting for Forgejo API responses."""

from __future__ import annotations

import json
from io import StringIO
from typing import Any

from rich.box import SIMPLE
from rich.console import Console
from rich.style import Style
from rich.table import Table
from rich.text import Text

_ROW_EVEN = Style(bgcolor="grey11")
_ROW_ODD = Style()


def _render(renderable: Any) -> str:
    """Render a Rich object to a plain string with ANSI codes."""
    buf = StringIO()
    console = Console(file=buf, force_terminal=True, width=120)
    console.print(renderable)
    return buf.getvalue().rstrip()


def _cell_value(row: dict[str, Any], key: str) -> str:
    """Extract a display value from a row dict, handling nested objects."""
    val = row.get(key, "")
    if isinstance(val, dict):
        return str(val.get("login", val.get("name", str(val))))
    return str(val)


def format_table(
    rows: list[dict[str, Any]],
    columns: list[tuple[str, str]],
    title: str | None = None,
) -> str:
    """Render a list of dicts as a Rich table.

    Uses a borderless style with alternating row background colors for
    readability.

    Args:
        rows: List of row dicts.
        columns: List of (key, header_label) tuples.
        title: Optional table title.
    """
    table = Table(
        title=title,
        box=SIMPLE,
        show_edge=False,
        header_style="bold",
        expand=True,
    )
    for _, header in columns:
        table.add_column(header)
    for i, row in enumerate(rows):
        style = _ROW_EVEN if i % 2 == 0 else _ROW_ODD
        table.add_row(*[_cell_value(row, k) for k, _ in columns], style=style)
    return _render(table)


def format_repo(repo: dict[str, Any]) -> str:
    """Format a single repository for detailed view."""
    lines = Text()
    lines.append(repo.get("full_name", ""), style="bold cyan")
    lines.append("\n")
    desc = repo.get("description", "")
    if desc:
        lines.append(desc + "\n", style="dim")
    lines.append(f"\nVisibility:  {'private' if repo.get('private') else 'public'}\n")
    lines.append(f"Stars:       {repo.get('stars_count', 0)}\n")
    lines.append(f"Forks:       {repo.get('forks_count', 0)}\n")
    lines.append(f"Language:    {repo.get('language', 'N/A')}\n")
    lines.append(f"Default:     {repo.get('default_branch', 'main')}\n")
    html_url = repo.get("html_url", "")
    if html_url:
        lines.append(f"URL:         {html_url}\n")
    return _render(lines)


def format_issue(issue: dict[str, Any]) -> str:
    """Format a single issue for detailed view."""
    lines = Text()
    number = issue.get("number", "?")
    title = issue.get("title", "")
    state = issue.get("state", "")
    lines.append(f"#{number} ", style="bold yellow")
    lines.append(title, style="bold")
    lines.append(f"  [{state}]", style="green" if state == "open" else "red")
    lines.append("\n")
    user = issue.get("user", {})
    lines.append(f"\nAuthor:      {user.get('login', 'unknown')}\n")
    labels = issue.get("labels", [])
    if labels:
        label_names = ", ".join(lb.get("name", "") for lb in labels)
        lines.append(f"Labels:      {label_names}\n")
    assignees = issue.get("assignees") or []
    if assignees:
        asgn = ", ".join(a.get("login", "") for a in assignees)
        lines.append(f"Assignees:   {asgn}\n")
    lines.append(f"Created:     {issue.get('created_at', '')}\n")
    body = issue.get("body", "")
    if body:
        lines.append(f"\n{body}\n")
    return _render(lines)


def format_pr(pr: dict[str, Any]) -> str:
    """Format a single pull request for detailed view."""
    lines = Text()
    number = pr.get("number", "?")
    title = pr.get("title", "")
    state = pr.get("state", "")
    lines.append(f"#{number} ", style="bold magenta")
    lines.append(title, style="bold")
    lines.append(f"  [{state}]", style="green" if state == "open" else "red")
    lines.append("\n")
    user = pr.get("user", {})
    lines.append(f"\nAuthor:      {user.get('login', 'unknown')}\n")
    lines.append(f"Head:        {pr.get('head', {}).get('label', '')}\n")
    lines.append(f"Base:        {pr.get('base', {}).get('label', '')}\n")
    lines.append(f"Mergeable:   {pr.get('mergeable', '')}\n")
    lines.append(f"Created:     {pr.get('created_at', '')}\n")
    body = pr.get("body", "")
    if body:
        lines.append(f"\n{body}\n")
    return _render(lines)


def format_release(release: dict[str, Any]) -> str:
    """Format a single release for detailed view."""
    lines = Text()
    tag = release.get("tag_name", "")
    name = release.get("name", tag)
    lines.append(name, style="bold green")
    if release.get("draft"):
        lines.append("  [draft]", style="yellow")
    if release.get("prerelease"):
        lines.append("  [prerelease]", style="yellow")
    lines.append("\n")
    lines.append(f"\nTag:         {tag}\n")
    author = release.get("author", {})
    lines.append(f"Author:      {author.get('login', 'unknown')}\n")
    lines.append(f"Published:   {release.get('published_at', release.get('created_at', ''))}\n")
    body = release.get("body", "")
    if body:
        lines.append(f"\n{body}\n")
    assets = release.get("assets", [])
    if assets:
        lines.append(f"\nAssets ({len(assets)}):\n")
        for asset in assets:
            lines.append(f"  - {asset.get('name', '')} ({asset.get('size', 0)} bytes)\n")
    return _render(lines)


def format_user(user: dict[str, Any]) -> str:
    """Format user info for auth status display."""
    lines = Text()
    lines.append("Logged in as ", style="dim")
    lines.append(user.get("login", "unknown"), style="bold green")
    lines.append("\n")
    full_name = user.get("full_name", "")
    if full_name:
        lines.append(f"Name:        {full_name}\n")
    lines.append(f"Email:       {user.get('email', 'N/A')}\n")
    lines.append(f"Admin:       {user.get('is_admin', False)}\n")
    return _render(lines)


def format_checks(pr_number: int, head_sha: str, runs: list[dict[str, Any]]) -> str:
    """Format CI check results for a pull request."""
    lines = Text()
    lines.append(f"Checks for PR #{pr_number}", style="bold magenta")
    lines.append(f"  (commit {head_sha[:12]})\n", style="dim")

    if not runs:
        lines.append("\nNo checks found.\n")
        return _render(lines)

    for run in runs:
        state = run.get("state", "unknown")
        style = {"success": "green", "pending": "yellow", "failure": "red", "error": "red"}.get(
            state, "white"
        )
        context = run.get("context", "unknown")
        lines.append(f"\n  [{state}] ", style=style)
        lines.append(context, style="bold")
        desc = run.get("description", "")
        if desc:
            lines.append(f"  — {desc}", style="dim")
        lines.append("\n")

        steps = run.get("steps", [])
        for step in steps:
            step_status = step.get("status", "unknown")
            step_style = {
                "success": "green",
                "running": "yellow",
                "failure": "red",
                "skipped": "dim",
            }.get(step_status, "white")
            duration = step.get("duration", "")
            dur_str = f" ({duration})" if duration else ""
            lines.append(f"    [{step_status}] ", style=step_style)
            lines.append(f"{step.get('name', '')}{dur_str}\n")

            log = step.get("log", "")
            if log and step_status == "failure":
                # Show last 30 lines of log for failed steps
                log_lines = log.strip().split("\n")
                tail = log_lines[-30:]
                for ll in tail:
                    lines.append(f"      {ll}\n", style="dim")

    return _render(lines)


def format_json(data: Any) -> str:
    """Pretty-print JSON data."""
    return json.dumps(data, indent=2, default=str)


def format_package(pkg: dict[str, Any]) -> str:
    """Format a single package for detailed view."""
    lines = Text()
    lines.append(pkg.get("name", ""), style="bold cyan")
    lines.append(f"  [{pkg.get('type', '')}]", style="yellow")
    lines.append("\n")
    lines.append(f"\nVersion:     {pkg.get('version', 'N/A')}\n")
    creator = pkg.get("creator", {})
    if creator:
        lines.append(f"Creator:     {creator.get('login', 'unknown')}\n")
    lines.append(f"Created:     {pkg.get('created_at', '')}\n")
    repo = pkg.get("repository")
    if repo:
        lines.append(f"Repository:  {repo.get('full_name', '')}\n")
    html_url = pkg.get("html_url", "")
    if html_url:
        lines.append(f"URL:         {html_url}\n")
    return _render(lines)


def format_run(data: dict[str, Any]) -> str:
    """Format action run state info (from web UI response)."""
    lines = Text()
    state = data.get("state", {})
    steps = state.get("steps", [])
    if not steps:
        return format_json(data)
    for i, step in enumerate(steps):
        status = step.get("status", "unknown")
        name = step.get("name", f"Step {i}")
        style = "green" if status == "success" else "red" if status == "failure" else "yellow"
        lines.append(f"  [{status:>10}] ", style=style)
        lines.append(f"{name}\n")
    return _render(lines)


def format_run_detail(run: dict[str, Any]) -> str:
    """Format a single action run for detailed view."""
    lines = Text()
    index = run.get("index_in_repo", run.get("id", "?"))
    title = run.get("title", "")
    status = run.get("status", "")
    style = "green" if status == "success" else "red" if status == "failure" else "yellow"
    lines.append(f"Run #{index} ", style="bold cyan")
    lines.append(title, style="bold")
    lines.append(f"  [{status}]", style=style)
    lines.append("\n")
    lines.append(f"\nEvent:       {run.get('event', '')}\n")
    lines.append(f"Workflow:    {run.get('workflow_id', '')}\n")
    lines.append(f"Ref:         {run.get('prettyref', '')}\n")
    lines.append(f"SHA:         {run.get('commit_sha', '')[:12]}\n")
    trigger_user = run.get("trigger_user", {})
    if trigger_user:
        lines.append(f"Triggered:   {trigger_user.get('login', 'unknown')}\n")
    lines.append(f"Started:     {run.get('started', '')}\n")
    lines.append(f"Stopped:     {run.get('stopped', '')}\n")
    html_url = run.get("html_url", "")
    if html_url:
        lines.append(f"URL:         {html_url}\n")
    return _render(lines)


def format_org(org: dict[str, Any]) -> str:
    """Format a single organization for detailed view."""
    lines = Text()
    lines.append(org.get("username", org.get("name", "")), style="bold cyan")
    lines.append("\n")
    desc = org.get("description", "")
    if desc:
        lines.append(desc + "\n", style="dim")
    lines.append(f"\nVisibility:  {org.get('visibility', 'N/A')}\n")
    lines.append(f"Location:    {org.get('location', 'N/A')}\n")
    website = org.get("website", "")
    if website:
        lines.append(f"Website:     {website}\n")
    return _render(lines)
