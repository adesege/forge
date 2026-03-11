"""Rich-based output formatting for Forgejo API responses."""

from __future__ import annotations

import json
from io import StringIO
from typing import Any

from rich.console import Console
from rich.table import Table
from rich.text import Text


def _render(renderable: Any) -> str:
    """Render a Rich object to a plain string with ANSI codes."""
    buf = StringIO()
    console = Console(file=buf, force_terminal=True, width=120)
    console.print(renderable)
    return buf.getvalue().rstrip()


def format_table(
    rows: list[dict[str, Any]],
    columns: list[tuple[str, str]],
    title: str | None = None,
) -> str:
    """Render a list of dicts as a Rich table.

    Args:
        rows: List of row dicts.
        columns: List of (key, header_label) tuples.
        title: Optional table title.
    """
    table = Table(title=title, show_lines=False)
    for _, header in columns:
        table.add_column(header)
    for row in rows:
        table.add_row(*[str(row.get(k, "")) for k, _ in columns])
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


def format_json(data: Any) -> str:
    """Pretty-print JSON data."""
    return json.dumps(data, indent=2, default=str)


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
