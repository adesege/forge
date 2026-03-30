"""CLI entry point for forge."""

from __future__ import annotations

import logging
import sys

import click
import structlog

from forge.config import load_config
from forge.secrets import (
    create as secrets_create,
)
from forge.secrets import (
    ensure as secrets_ensure,
)
from forge.secrets import (
    get as secrets_get,
)
from forge.secrets import (
    remove as secrets_remove,
)
from forge.secrets import (
    status as secrets_status,
)
from forge.services import (
    actions,
    auth,
    completion,
    install,
    issue,
    org,
    package,
    pr,
    release,
    repo,
)


def setup_logging(level: str = "INFO", service_name: str = "") -> None:
    """Configure structured logging."""
    log_level = getattr(logging, level.upper(), logging.INFO)

    shared_processors: list[structlog.types.Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.UnicodeDecoder(),
    ]

    structlog.configure(
        processors=[
            *shared_processors,
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    formatter = structlog.stdlib.ProcessorFormatter(
        processors=[
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            structlog.dev.ConsoleRenderer(),
        ],
    )

    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.addHandler(handler)
    root_logger.setLevel(log_level)

    if service_name:
        structlog.contextvars.bind_contextvars(service=service_name)


@click.group()
@click.version_option(prog_name="forge")
@click.option("--config", "config_path", default=None, help="Path to config.toml")
@click.option("--log-level", default="INFO", help="Log level")
@click.pass_context
def main(ctx: click.Context, config_path: str | None, log_level: str) -> None:
    """forge — Forgejo CLI and MCP tool"""
    ctx.ensure_object(dict)
    ctx.obj["config"] = load_config(config_path, env_prefix="FORGE_", app_name="forge")
    setup_logging(level=log_level, service_name="forge")


# ── Auth ─────────────────────────────────────────────────────────────────────


@main.group("auth")
def auth_group() -> None:
    """Manage Forgejo authentication."""


@auth_group.command("status")
def auth_status() -> None:
    """Check authentication status and display the logged-in user."""
    click.echo(auth.status())


@auth_group.command("token")
def auth_token() -> None:
    """Display the configured API token (masked)."""
    click.echo(auth.token())


# ── CI / Actions ─────────────────────────────────────────────────────────────


@main.group("ci")
def ci_group() -> None:
    """CI/CD action runs and logs."""


@ci_group.command("runs")
@click.option("--owner", default="", help="Repository owner")
@click.option("--repo", "repo_name", default="", help="Repository name")
@click.option("--status", default="", help="Filter by status (success/failure/running/waiting)")
@click.option("--event", default="", help="Filter by event (push/pull_request/workflow_dispatch)")
@click.option("--limit", default=30, help="Max results")
@click.option("--page", default=1, help="Page number")
def ci_runs(owner: str, repo_name: str, status: str, event: str, limit: int, page: int) -> None:
    """List action runs."""
    click.echo(
        actions.list_runs(
            owner=owner, repo=repo_name, status=status, event=event, limit=limit, page=page
        )
    )


@ci_group.command("view")
@click.option("--run-id", default=0, type=int, help="Action run ID")
@click.option("--owner", default="", help="Repository owner")
@click.option("--repo", "repo_name", default="", help="Repository name")
def ci_view(run_id: int, owner: str, repo_name: str) -> None:
    """View action run details."""
    click.echo(actions.view_run(run_id=run_id, owner=owner, repo=repo_name))


@ci_group.command("log")
@click.option("--run-id", default=0, type=int, help="Action run ID")
@click.option("--job", default=0, type=int, help="Job index (default: 0)")
@click.option("--step", default=0, type=int, help="Step index to show logs for")
@click.option("--owner", default="", help="Repository owner")
@click.option("--repo", "repo_name", default="", help="Repository name")
def ci_log(run_id: int, job: int, step: int, owner: str, repo_name: str) -> None:
    """Get log output for a CI run step."""
    click.echo(actions.log(run_id=run_id, job=job, step=step, owner=owner, repo=repo_name))


@ci_group.command("status")
@click.option("--ref", default="", help="Branch, tag, or commit SHA")
@click.option("--owner", default="", help="Repository owner")
@click.option("--repo", "repo_name", default="", help="Repository name")
def ci_status(ref: str, owner: str, repo_name: str) -> None:
    """Get commit statuses (CI checks) for a ref."""
    click.echo(actions.commit_status(ref=ref, owner=owner, repo=repo_name))


# ── Completion ───────────────────────────────────────────────────────────────


@main.group("completion")
def completion_group() -> None:
    """Shell completion scripts."""


@completion_group.command("bash")
def completion_bash() -> None:
    """Generate bash completion script."""
    click.echo(completion.bash())


@completion_group.command("zsh")
def completion_zsh() -> None:
    """Generate zsh completion script."""
    click.echo(completion.zsh())


@completion_group.command("fish")
def completion_fish() -> None:
    """Generate fish completion script."""
    click.echo(completion.fish())


# ── Repo ─────────────────────────────────────────────────────────────────────


@main.group("repo")
def repo_group() -> None:
    """Manage repositories."""


@repo_group.command("list")
@click.option("--owner", default="", help="Repository owner")
@click.option("--limit", default=30, help="Max results")
@click.option("--page", default=1, help="Page number")
def repo_list(owner: str, limit: int, page: int) -> None:
    """List repositories."""
    click.echo(repo.list_repos(owner=owner, limit=limit, page=page))


@repo_group.command("view")
@click.option("--owner", default="", help="Repository owner")
@click.option("--repo", "repo_name", default="", help="Repository name")
def repo_view(owner: str, repo_name: str) -> None:
    """View repository details."""
    click.echo(repo.view(owner=owner, repo=repo_name))


@repo_group.command("create")
@click.option("--name", default="", help="Repository name (defaults to CWD basename)")
@click.option("--description", default="", help="Repository description")
@click.option("--private", is_flag=True, help="Make repository private")
@click.option("--org", default="", help="Create under this organization")
def repo_create(name: str, description: str, private: bool, org: str) -> None:
    """Create a new repository."""
    click.echo(repo.create(name=name, description=description, private=private, org=org))


@repo_group.command("clone")
@click.option("--name", default="", help="Repository name")
@click.option("--owner", default="", help="Repository owner")
@click.option("--directory", default="", help="Clone into this directory")
def repo_clone(name: str, owner: str, directory: str) -> None:
    """Clone a repository."""
    click.echo(repo.clone(name=name, owner=owner, directory=directory))


@repo_group.command("fork")
@click.option("--owner", default="", help="Source repository owner")
@click.option("--repo", "repo_name", default="", help="Source repository name")
@click.option("--org", default="", help="Fork into this organization")
def repo_fork(owner: str, repo_name: str, org: str) -> None:
    """Fork a repository."""
    click.echo(repo.fork(owner=owner, repo=repo_name, org=org))


@repo_group.command("delete")
@click.option("--owner", default="", help="Repository owner")
@click.option("--repo", "repo_name", default="", help="Repository name")
def repo_delete(owner: str, repo_name: str) -> None:
    """Delete a repository."""
    click.echo(repo.delete(owner=owner, repo=repo_name))


@repo_group.command("search")
@click.option("--query", default="", help="Search query")
@click.option("--limit", default=30, help="Max results")
def repo_search(query: str, limit: int) -> None:
    """Search repositories."""
    click.echo(repo.search(query=query, limit=limit))


# ── Issue ────────────────────────────────────────────────────────────────────


@main.group("issue")
def issue_group() -> None:
    """Manage issues."""


@issue_group.command("list")
@click.option("--owner", default="", help="Repository owner")
@click.option("--repo", "repo_name", default="", help="Repository name")
@click.option("--state", default="open", help="Issue state (open/closed)")
@click.option("--labels", default="", help="Filter by labels (comma-separated)")
@click.option("--milestone", default="", help="Filter by milestone")
@click.option("--limit", default=30, help="Max results")
@click.option("--page", default=1, help="Page number")
def issue_list(
    owner: str, repo_name: str, state: str, labels: str, milestone: str, limit: int, page: int
) -> None:
    """List issues."""
    click.echo(
        issue.list_issues(
            owner=owner,
            repo=repo_name,
            state=state,
            labels=labels,
            milestone=milestone,
            limit=limit,
            page=page,
        )
    )


@issue_group.command("view")
@click.option("--number", default=0, type=int, help="Issue number")
@click.option("--owner", default="", help="Repository owner")
@click.option("--repo", "repo_name", default="", help="Repository name")
def issue_view(number: int, owner: str, repo_name: str) -> None:
    """View issue details."""
    click.echo(issue.view(number=number, owner=owner, repo=repo_name))


@issue_group.command("create")
@click.option("--title", default="", help="Issue title")
@click.option("--body", default="", help="Issue body")
@click.option("--labels", default="", help="Labels (comma-separated)")
@click.option("--assignees", default="", help="Assignees (comma-separated)")
@click.option("--milestone", default=0, type=int, help="Milestone ID")
@click.option("--owner", default="", help="Repository owner")
@click.option("--repo", "repo_name", default="", help="Repository name")
def issue_create(
    title: str, body: str, labels: str, assignees: str, milestone: int, owner: str, repo_name: str
) -> None:
    """Create an issue."""
    click.echo(
        issue.create(
            title=title,
            body=body,
            labels=labels,
            assignees=assignees,
            milestone=milestone,
            owner=owner,
            repo=repo_name,
        )
    )


@issue_group.command("close")
@click.option("--number", default=0, type=int, help="Issue number")
@click.option("--owner", default="", help="Repository owner")
@click.option("--repo", "repo_name", default="", help="Repository name")
def issue_close(number: int, owner: str, repo_name: str) -> None:
    """Close an issue."""
    click.echo(issue.close(number=number, owner=owner, repo=repo_name))


@issue_group.command("reopen")
@click.option("--number", default=0, type=int, help="Issue number")
@click.option("--owner", default="", help="Repository owner")
@click.option("--repo", "repo_name", default="", help="Repository name")
def issue_reopen(number: int, owner: str, repo_name: str) -> None:
    """Reopen a closed issue."""
    click.echo(issue.reopen(number=number, owner=owner, repo=repo_name))


@issue_group.command("comment")
@click.option("--number", default=0, type=int, help="Issue number")
@click.option("--body", default="", help="Comment body")
@click.option("--owner", default="", help="Repository owner")
@click.option("--repo", "repo_name", default="", help="Repository name")
def issue_comment(number: int, body: str, owner: str, repo_name: str) -> None:
    """Add a comment to an issue."""
    click.echo(issue.comment(number=number, body=body, owner=owner, repo=repo_name))


@issue_group.command("edit")
@click.option("--number", default=0, type=int, help="Issue number")
@click.option("--title", default="", help="New title")
@click.option("--body", default="", help="New body")
@click.option("--owner", default="", help="Repository owner")
@click.option("--repo", "repo_name", default="", help="Repository name")
def issue_edit(number: int, title: str, body: str, owner: str, repo_name: str) -> None:
    """Edit an issue."""
    click.echo(issue.edit(number=number, title=title, body=body, owner=owner, repo=repo_name))


# ── PR ───────────────────────────────────────────────────────────────────────


@main.group("pr")
def pr_group() -> None:
    """Manage pull requests."""


@pr_group.command("list")
@click.option("--owner", default="", help="Repository owner")
@click.option("--repo", "repo_name", default="", help="Repository name")
@click.option("--state", default="open", help="PR state (open/closed)")
@click.option("--limit", default=30, help="Max results")
@click.option("--page", default=1, help="Page number")
def pr_list(owner: str, repo_name: str, state: str, limit: int, page: int) -> None:
    """List pull requests."""
    click.echo(pr.list_prs(owner=owner, repo=repo_name, state=state, limit=limit, page=page))


@pr_group.command("view")
@click.option("--number", default=0, type=int, help="PR number")
@click.option("--owner", default="", help="Repository owner")
@click.option("--repo", "repo_name", default="", help="Repository name")
def pr_view(number: int, owner: str, repo_name: str) -> None:
    """View pull request details."""
    click.echo(pr.view(number=number, owner=owner, repo=repo_name))


@pr_group.command("create")
@click.option("--title", default="", help="PR title")
@click.option("--body", default="", help="PR body")
@click.option("--head", default="", help="Source branch")
@click.option("--base", default="main", help="Target branch")
@click.option("--owner", default="", help="Repository owner")
@click.option("--repo", "repo_name", default="", help="Repository name")
def pr_create(title: str, body: str, head: str, base: str, owner: str, repo_name: str) -> None:
    """Create a pull request."""
    click.echo(pr.create(title=title, body=body, head=head, base=base, owner=owner, repo=repo_name))


@pr_group.command("merge")
@click.option("--number", default=0, type=int, help="PR number")
@click.option("--method", default="merge", help="Merge method (merge/rebase/squash)")
@click.option("--owner", default="", help="Repository owner")
@click.option("--repo", "repo_name", default="", help="Repository name")
def pr_merge(number: int, method: str, owner: str, repo_name: str) -> None:
    """Merge a pull request."""
    click.echo(pr.merge(number=number, method=method, owner=owner, repo=repo_name))


@pr_group.command("close")
@click.option("--number", default=0, type=int, help="PR number")
@click.option("--owner", default="", help="Repository owner")
@click.option("--repo", "repo_name", default="", help="Repository name")
def pr_close(number: int, owner: str, repo_name: str) -> None:
    """Close a pull request."""
    click.echo(pr.close(number=number, owner=owner, repo=repo_name))


@pr_group.command("reopen")
@click.option("--number", default=0, type=int, help="PR number")
@click.option("--owner", default="", help="Repository owner")
@click.option("--repo", "repo_name", default="", help="Repository name")
def pr_reopen(number: int, owner: str, repo_name: str) -> None:
    """Reopen a closed pull request."""
    click.echo(pr.reopen(number=number, owner=owner, repo=repo_name))


@pr_group.command("diff")
@click.option("--number", default=0, type=int, help="PR number")
@click.option("--owner", default="", help="Repository owner")
@click.option("--repo", "repo_name", default="", help="Repository name")
def pr_diff(number: int, owner: str, repo_name: str) -> None:
    """View the diff of a pull request."""
    click.echo(pr.diff(number=number, owner=owner, repo=repo_name))


@pr_group.command("review")
@click.option("--number", default=0, type=int, help="PR number")
@click.option("--body", default="", help="Review body")
@click.option("--event", default="COMMENT", help="Event type (APPROVE/REQUEST_CHANGES/COMMENT)")
@click.option("--owner", default="", help="Repository owner")
@click.option("--repo", "repo_name", default="", help="Repository name")
def pr_review(number: int, body: str, event: str, owner: str, repo_name: str) -> None:
    """Submit a review on a pull request."""
    click.echo(pr.review(number=number, body=body, event=event, owner=owner, repo=repo_name))


# ── Release ──────────────────────────────────────────────────────────────────


@main.group("release")
def release_group() -> None:
    """Manage releases."""


@release_group.command("list")
@click.option("--owner", default="", help="Repository owner")
@click.option("--repo", "repo_name", default="", help="Repository name")
@click.option("--limit", default=30, help="Max results")
@click.option("--page", default=1, help="Page number")
def release_list(owner: str, repo_name: str, limit: int, page: int) -> None:
    """List releases."""
    click.echo(release.list_releases(owner=owner, repo=repo_name, limit=limit, page=page))


@release_group.command("view")
@click.option("--tag", default="", help="Release tag")
@click.option("--owner", default="", help="Repository owner")
@click.option("--repo", "repo_name", default="", help="Repository name")
def release_view(tag: str, owner: str, repo_name: str) -> None:
    """View release details."""
    click.echo(release.view(tag=tag, owner=owner, repo=repo_name))


@release_group.command("create")
@click.option("--tag", default="", help="Release tag")
@click.option("--title", default="", help="Release title")
@click.option("--body", default="", help="Release notes")
@click.option("--draft", is_flag=True, help="Create as draft")
@click.option("--prerelease", is_flag=True, help="Mark as prerelease")
@click.option("--owner", default="", help="Repository owner")
@click.option("--repo", "repo_name", default="", help="Repository name")
def release_create(
    tag: str, title: str, body: str, draft: bool, prerelease: bool, owner: str, repo_name: str
) -> None:
    """Create a release."""
    click.echo(
        release.create(
            tag=tag,
            title=title,
            body=body,
            draft=draft,
            prerelease=prerelease,
            owner=owner,
            repo=repo_name,
        )
    )


@release_group.command("delete")
@click.option("--tag", default="", help="Release tag")
@click.option("--owner", default="", help="Repository owner")
@click.option("--repo", "repo_name", default="", help="Repository name")
def release_delete(tag: str, owner: str, repo_name: str) -> None:
    """Delete a release."""
    click.echo(release.delete(tag=tag, owner=owner, repo=repo_name))


@release_group.command("edit")
@click.option("--tag", default="", help="Release tag")
@click.option("--title", default="", help="New title")
@click.option("--body", default="", help="New release notes")
@click.option("--draft", is_flag=True, help="Mark as draft")
@click.option("--prerelease", is_flag=True, help="Mark as prerelease")
@click.option("--owner", default="", help="Repository owner")
@click.option("--repo", "repo_name", default="", help="Repository name")
def release_edit(
    tag: str, title: str, body: str, draft: bool, prerelease: bool, owner: str, repo_name: str
) -> None:
    """Edit a release."""
    click.echo(
        release.edit(
            tag=tag,
            title=title,
            body=body,
            draft=draft,
            prerelease=prerelease,
            owner=owner,
            repo=repo_name,
        )
    )


# ── Org ──────────────────────────────────────────────────────────────────────


@main.group("org")
def org_group() -> None:
    """Manage organizations."""


@org_group.command("list")
def org_list() -> None:
    """List organizations."""
    click.echo(org.list_orgs())


@org_group.command("view")
@click.option("--org", "org_name", default="", help="Organization name")
def org_view(org_name: str) -> None:
    """View organization details."""
    click.echo(org.view(org=org_name))


@org_group.command("repos")
@click.option("--org", "org_name", default="", help="Organization name")
@click.option("--limit", default=30, help="Max results")
@click.option("--page", default=1, help="Page number")
def org_repos(org_name: str, limit: int, page: int) -> None:
    """List repositories in an organization."""
    click.echo(org.repos(org=org_name, limit=limit, page=page))


@org_group.command("members")
@click.option("--org", "org_name", default="", help="Organization name")
@click.option("--limit", default=30, help="Max results")
@click.option("--page", default=1, help="Page number")
def org_members(org_name: str, limit: int, page: int) -> None:
    """List members of an organization."""
    click.echo(org.members(org=org_name, limit=limit, page=page))


# ── Package ──────────────────────────────────────────────────────────────────


@main.group("package")
def package_group() -> None:
    """Manage packages."""


@package_group.command("list")
@click.option("--owner", default="", help="Package owner")
@click.option("--type", "pkg_type", default="", help="Package type (generic/pypi/npm/debian)")
@click.option("--query", default="", help="Search query")
@click.option("--limit", default=30, help="Max results")
@click.option("--page", default=1, help="Page number")
def package_list(owner: str, pkg_type: str, query: str, limit: int, page: int) -> None:
    """List packages."""
    click.echo(
        package.list_packages(owner=owner, type=pkg_type, query=query, limit=limit, page=page)
    )


@package_group.command("view")
@click.option("--name", default="", help="Package name")
@click.option("--version", default="", help="Package version")
@click.option("--type", "pkg_type", default="", help="Package type")
@click.option("--owner", default="", help="Package owner")
def package_view(name: str, version: str, pkg_type: str, owner: str) -> None:
    """View package details."""
    click.echo(package.view_package(name=name, version=version, type=pkg_type, owner=owner))


@package_group.command("files")
@click.option("--name", default="", help="Package name")
@click.option("--version", default="", help="Package version")
@click.option("--type", "pkg_type", default="", help="Package type")
@click.option("--owner", default="", help="Package owner")
def package_files(name: str, version: str, pkg_type: str, owner: str) -> None:
    """List files in a package version."""
    click.echo(package.files(name=name, version=version, type=pkg_type, owner=owner))


@package_group.command("delete")
@click.option("--name", default="", help="Package name")
@click.option("--version", default="", help="Package version")
@click.option("--type", "pkg_type", default="", help="Package type")
@click.option("--owner", default="", help="Package owner")
def package_delete(name: str, version: str, pkg_type: str, owner: str) -> None:
    """Delete a package version."""
    click.echo(package.delete_package(name=name, version=version, type=pkg_type, owner=owner))


@package_group.command("publish")
@click.option("--name", default="", help="Package name")
@click.option("--version", default="", help="Package version")
@click.option("--file", "filepath", default="", help="File to upload")
@click.option("--owner", default="", help="Package owner")
def package_publish(name: str, version: str, filepath: str, owner: str) -> None:
    """Publish to generic package registry."""
    click.echo(package.publish(name=name, version=version, file=filepath, owner=owner))


@package_group.command("publish-deb")
@click.option("--file", "filepath", default="", help=".deb file to upload")
@click.option("--owner", default="", help="Package owner")
@click.option("--distribution", default="trixie", help="Debian distribution")
@click.option("--component", default="main", help="Repository component")
def package_publish_deb(filepath: str, owner: str, distribution: str, component: str) -> None:
    """Publish a .deb package."""
    click.echo(
        package.publish_deb(
            file=filepath, owner=owner, distribution=distribution, component=component
        )
    )


@package_group.command("publish-crate")
@click.option("--file", "filepath", default="", help=".crate file to upload")
@click.option("--owner", default="", help="Package owner")
def package_publish_crate(filepath: str, owner: str) -> None:
    """Publish a Rust crate."""
    click.echo(package.publish_crate(file=filepath, owner=owner))


@package_group.command("download")
@click.option("--name", default="", help="Package name")
@click.option("--version", default="", help="Package version")
@click.option("--filename", default="", help="File to download")
@click.option("--output", default="", help="Output path")
@click.option("--owner", default="", help="Package owner")
def package_download(name: str, version: str, filename: str, output: str, owner: str) -> None:
    """Download from generic package registry."""
    click.echo(
        package.download(name=name, version=version, filename=filename, output=output, owner=owner)
    )


# ── Install ──────────────────────────────────────────────────────────────────


@main.group("install")
def install_group() -> None:
    """Configure package repositories."""


@install_group.command("pypi")
@click.option("--owner", default="", help="Package owner")
def install_pypi(owner: str) -> None:
    """Add the Forgejo PyPI index to uv."""
    click.echo(install.pypi(owner=owner))


@install_group.command("debian")
@click.option("--owner", default="", help="Package owner")
@click.option("--codename", default="", help="Debian codename")
def install_debian(owner: str, codename: str) -> None:
    """Add the Forgejo Debian repository."""
    click.echo(install.debian(owner=owner, codename=codename))


# ── Secrets ──────────────────────────────────────────────────────────────────


@main.group("secrets")
def secrets_group() -> None:
    """Manage 1Password secrets."""


@secrets_group.command("status")
def secrets_status_cmd() -> None:
    """Check if 1Password CLI is available."""
    click.echo(secrets_status())


@secrets_group.command("get")
@click.argument("vault")
@click.argument("title")
@click.option("--field", default="", help="Specific field to retrieve")
def secrets_get_cmd(vault: str, title: str, field: str) -> None:
    """Get a secret from 1Password."""
    click.echo(secrets_get(vault, title, field=field))


@secrets_group.command("create")
@click.argument("vault")
@click.argument("title")
@click.argument("key")
@click.argument("value")
def secrets_create_cmd(vault: str, title: str, key: str, value: str) -> None:
    """Create a new secret in 1Password."""
    click.echo(secrets_create(vault, title, key, value))


@secrets_group.command("ensure")
@click.argument("vault")
@click.argument("title")
@click.argument("key")
@click.argument("value")
def secrets_ensure_cmd(vault: str, title: str, key: str, value: str) -> None:
    """Create or update a secret in 1Password (idempotent)."""
    click.echo(secrets_ensure(vault, title, key, value))


@secrets_group.command("remove")
@click.argument("vault")
@click.argument("title")
def secrets_remove_cmd(vault: str, title: str) -> None:
    """Delete a secret from 1Password."""
    click.echo(secrets_remove(vault, title))
