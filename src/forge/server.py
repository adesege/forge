"""MCP server for forge.

Exposes service functions as MCP tools.
"""

from __future__ import annotations

from fastmcp import FastMCP

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


def create_mcp() -> FastMCP:
    """Create the FastMCP server with service tools."""
    mcp = FastMCP("forge")

    # ── CI / Actions ─────────────────────────────────────────────────────

    @mcp.tool(name="ci_runs", description="List CI/CD action runs for a repository")
    def ci_runs(
        owner: str = "",
        repo_name: str = "",
        status: str = "",
        event: str = "",
        limit: int = 30,
        page: int = 1,
    ) -> str:
        return actions.list_runs(
            owner=owner, repo=repo_name, status=status, event=event, limit=limit, page=page
        )

    @mcp.tool(name="ci_view", description="View action run details")
    def ci_view(run_id: int = 0, owner: str = "", repo_name: str = "") -> str:
        return actions.view_run(run_id=run_id, owner=owner, repo=repo_name)

    @mcp.tool(name="ci_log", description="Get log output for a CI run job")
    def ci_log(run_id: int = 0, job: int = 0, owner: str = "", repo_name: str = "") -> str:
        return actions.log(run_id=run_id, job=job, owner=owner, repo=repo_name)

    @mcp.tool(name="ci_status", description="Get commit statuses (CI checks) for a ref")
    def ci_status(ref: str = "", owner: str = "", repo_name: str = "") -> str:
        return actions.commit_status(ref=ref, owner=owner, repo=repo_name)

    # ── Auth ─────────────────────────────────────────────────────────────

    @mcp.tool(name="auth_status", description="Check Forgejo authentication status")
    def auth_status() -> str:
        return auth.status()

    @mcp.tool(name="auth_token", description="Display the configured API token (masked)")
    def auth_token() -> str:
        return auth.token()

    # ── Completion ───────────────────────────────────────────────────────

    @mcp.tool(name="completion_bash", description="Generate bash completion script")
    def completion_bash() -> str:
        return completion.bash()

    @mcp.tool(name="completion_zsh", description="Generate zsh completion script")
    def completion_zsh() -> str:
        return completion.zsh()

    @mcp.tool(name="completion_fish", description="Generate fish completion script")
    def completion_fish() -> str:
        return completion.fish()

    # ── Repo ─────────────────────────────────────────────────────────────

    @mcp.tool(name="repo_list", description="List repositories")
    def repo_list(owner: str = "", limit: int = 30, page: int = 1) -> str:
        return repo.list_repos(owner=owner, limit=limit, page=page)

    @mcp.tool(name="repo_view", description="View repository details")
    def repo_view(owner: str = "", repo_name: str = "") -> str:
        return repo.view(owner=owner, repo=repo_name)

    @mcp.tool(name="repo_create", description="Create a new repository")
    def repo_create(
        name: str = "", description: str = "", private: bool = False, org: str = ""
    ) -> str:
        return repo.create(name=name, description=description, private=private, org=org)

    @mcp.tool(name="repo_clone", description="Clone a repository")
    def repo_clone(name: str = "", owner: str = "", directory: str = "") -> str:
        return repo.clone(name=name, owner=owner, directory=directory)

    @mcp.tool(name="repo_fork", description="Fork a repository")
    def repo_fork(owner: str = "", repo_name: str = "", org: str = "") -> str:
        return repo.fork(owner=owner, repo=repo_name, org=org)

    @mcp.tool(name="repo_delete", description="Delete a repository")
    def repo_delete(owner: str = "", repo_name: str = "") -> str:
        return repo.delete(owner=owner, repo=repo_name)

    @mcp.tool(name="repo_search", description="Search repositories")
    def repo_search(query: str = "", limit: int = 30) -> str:
        return repo.search(query=query, limit=limit)

    # ── Issue ────────────────────────────────────────────────────────────

    @mcp.tool(name="issue_list", description="List issues")
    def issue_list(
        owner: str = "",
        repo_name: str = "",
        state: str = "open",
        labels: str = "",
        milestone: str = "",
        limit: int = 30,
        page: int = 1,
    ) -> str:
        return issue.list_issues(
            owner=owner,
            repo=repo_name,
            state=state,
            labels=labels,
            milestone=milestone,
            limit=limit,
            page=page,
        )

    @mcp.tool(name="issue_view", description="View issue details")
    def issue_view(number: int = 0, owner: str = "", repo_name: str = "") -> str:
        return issue.view(number=number, owner=owner, repo=repo_name)

    @mcp.tool(name="issue_create", description="Create an issue")
    def issue_create(
        title: str = "",
        body: str = "",
        labels: str = "",
        assignees: str = "",
        milestone: int = 0,
        owner: str = "",
        repo_name: str = "",
    ) -> str:
        return issue.create(
            title=title,
            body=body,
            labels=labels,
            assignees=assignees,
            milestone=milestone,
            owner=owner,
            repo=repo_name,
        )

    @mcp.tool(name="issue_close", description="Close an issue")
    def issue_close(number: int = 0, owner: str = "", repo_name: str = "") -> str:
        return issue.close(number=number, owner=owner, repo=repo_name)

    @mcp.tool(name="issue_reopen", description="Reopen a closed issue")
    def issue_reopen(number: int = 0, owner: str = "", repo_name: str = "") -> str:
        return issue.reopen(number=number, owner=owner, repo=repo_name)

    @mcp.tool(name="issue_comment", description="Add a comment to an issue")
    def issue_comment(number: int = 0, body: str = "", owner: str = "", repo_name: str = "") -> str:
        return issue.comment(number=number, body=body, owner=owner, repo=repo_name)

    @mcp.tool(name="issue_edit", description="Edit an issue")
    def issue_edit(
        number: int = 0, title: str = "", body: str = "", owner: str = "", repo_name: str = ""
    ) -> str:
        return issue.edit(number=number, title=title, body=body, owner=owner, repo=repo_name)

    # ── PR ───────────────────────────────────────────────────────────────

    @mcp.tool(name="pr_list", description="List pull requests")
    def pr_list(
        owner: str = "",
        repo_name: str = "",
        state: str = "open",
        limit: int = 30,
        page: int = 1,
    ) -> str:
        return pr.list_prs(owner=owner, repo=repo_name, state=state, limit=limit, page=page)

    @mcp.tool(name="pr_view", description="View pull request details")
    def pr_view(number: int = 0, owner: str = "", repo_name: str = "") -> str:
        return pr.view(number=number, owner=owner, repo=repo_name)

    @mcp.tool(name="pr_create", description="Create a pull request")
    def pr_create(
        title: str = "",
        body: str = "",
        head: str = "",
        base: str = "main",
        owner: str = "",
        repo_name: str = "",
    ) -> str:
        return pr.create(title=title, body=body, head=head, base=base, owner=owner, repo=repo_name)

    @mcp.tool(name="pr_merge", description="Merge a pull request")
    def pr_merge(
        number: int = 0, method: str = "merge", owner: str = "", repo_name: str = ""
    ) -> str:
        return pr.merge(number=number, method=method, owner=owner, repo=repo_name)

    @mcp.tool(name="pr_close", description="Close a pull request")
    def pr_close(number: int = 0, owner: str = "", repo_name: str = "") -> str:
        return pr.close(number=number, owner=owner, repo=repo_name)

    @mcp.tool(name="pr_reopen", description="Reopen a closed pull request")
    def pr_reopen(number: int = 0, owner: str = "", repo_name: str = "") -> str:
        return pr.reopen(number=number, owner=owner, repo=repo_name)

    @mcp.tool(name="pr_diff", description="View the diff of a pull request")
    def pr_diff(number: int = 0, owner: str = "", repo_name: str = "") -> str:
        return pr.diff(number=number, owner=owner, repo=repo_name)

    @mcp.tool(
        name="pr_checks",
        description="View CI check status, step details, and failure logs for a pull request",
    )
    def pr_checks(number: int = 0, owner: str = "", repo_name: str = "") -> str:
        return pr.checks(number=number, owner=owner, repo=repo_name)

    @mcp.tool(name="pr_review", description="Submit a review on a pull request")
    def pr_review(
        number: int = 0,
        body: str = "",
        event: str = "COMMENT",
        owner: str = "",
        repo_name: str = "",
    ) -> str:
        return pr.review(number=number, body=body, event=event, owner=owner, repo=repo_name)

    @mcp.tool(name="pr_react", description="Add a reaction to a PR comment")
    def pr_react(
        comment_id: str = "",
        reaction: str = "+1",
        owner: str = "",
        repo_name: str = "",
    ) -> str:
        return pr.react(comment_id=comment_id, reaction=reaction, owner=owner, repo=repo_name)

    # ── Release ──────────────────────────────────────────────────────────

    @mcp.tool(name="release_list", description="List releases")
    def release_list(owner: str = "", repo_name: str = "", limit: int = 30, page: int = 1) -> str:
        return release.list_releases(owner=owner, repo=repo_name, limit=limit, page=page)

    @mcp.tool(name="release_view", description="View release details")
    def release_view(tag: str = "", owner: str = "", repo_name: str = "") -> str:
        return release.view(tag=tag, owner=owner, repo=repo_name)

    @mcp.tool(name="release_create", description="Create a release")
    def release_create(
        tag: str = "",
        title: str = "",
        body: str = "",
        draft: bool = False,
        prerelease: bool = False,
        owner: str = "",
        repo_name: str = "",
    ) -> str:
        return release.create(
            tag=tag,
            title=title,
            body=body,
            draft=draft,
            prerelease=prerelease,
            owner=owner,
            repo=repo_name,
        )

    @mcp.tool(name="release_delete", description="Delete a release")
    def release_delete(tag: str = "", owner: str = "", repo_name: str = "") -> str:
        return release.delete(tag=tag, owner=owner, repo=repo_name)

    @mcp.tool(name="release_edit", description="Edit a release")
    def release_edit(
        tag: str = "",
        title: str = "",
        body: str = "",
        draft: bool = False,
        prerelease: bool = False,
        owner: str = "",
        repo_name: str = "",
    ) -> str:
        return release.edit(
            tag=tag,
            title=title,
            body=body,
            draft=draft,
            prerelease=prerelease,
            owner=owner,
            repo=repo_name,
        )

    # ── Org ──────────────────────────────────────────────────────────────

    @mcp.tool(name="org_list", description="List organizations")
    def org_list() -> str:
        return org.list_orgs()

    @mcp.tool(name="org_view", description="View organization details")
    def org_view(org_name: str = "") -> str:
        return org.view(org=org_name)

    @mcp.tool(name="org_repos", description="List repositories in an organization")
    def org_repos(org_name: str = "", limit: int = 30, page: int = 1) -> str:
        return org.repos(org=org_name, limit=limit, page=page)

    @mcp.tool(name="org_members", description="List members of an organization")
    def org_members(org_name: str = "", limit: int = 30, page: int = 1) -> str:
        return org.members(org=org_name, limit=limit, page=page)

    # ── Package ──────────────────────────────────────────────────────────

    @mcp.tool(name="package_list", description="List packages")
    def package_list(
        owner: str = "", type: str = "", query: str = "", limit: int = 30, page: int = 1
    ) -> str:
        return package.list_packages(owner=owner, type=type, query=query, limit=limit, page=page)

    @mcp.tool(name="package_view", description="View package details")
    def package_view(name: str = "", version: str = "", type: str = "", owner: str = "") -> str:
        return package.view_package(name=name, version=version, type=type, owner=owner)

    @mcp.tool(name="package_files", description="List files in a package version")
    def package_files(name: str = "", version: str = "", type: str = "", owner: str = "") -> str:
        return package.files(name=name, version=version, type=type, owner=owner)

    @mcp.tool(name="package_delete", description="Delete a package version")
    def package_delete(name: str = "", version: str = "", type: str = "", owner: str = "") -> str:
        return package.delete_package(name=name, version=version, type=type, owner=owner)

    @mcp.tool(name="package_publish", description="Publish to generic package registry")
    def package_publish(name: str = "", version: str = "", file: str = "", owner: str = "") -> str:
        return package.publish(name=name, version=version, file=file, owner=owner)

    @mcp.tool(name="package_publish_deb", description="Publish a .deb package")
    def package_publish_deb(
        file: str = "", owner: str = "", distribution: str = "trixie", component: str = "main"
    ) -> str:
        return package.publish_deb(
            file=file, owner=owner, distribution=distribution, component=component
        )

    @mcp.tool(name="package_publish_crate", description="Publish a Rust crate")
    def package_publish_crate(file: str = "", owner: str = "") -> str:
        return package.publish_crate(file=file, owner=owner)

    @mcp.tool(name="package_download", description="Download from generic package registry")
    def package_download(
        name: str = "", version: str = "", filename: str = "", output: str = "", owner: str = ""
    ) -> str:
        return package.download(
            name=name, version=version, filename=filename, output=output, owner=owner
        )

    # ── Install ──────────────────────────────────────────────────────────

    @mcp.tool(name="install_pypi", description="Add Forgejo PyPI index to uv")
    def install_pypi(owner: str = "") -> str:
        return install.pypi(owner=owner)

    @mcp.tool(name="install_debian", description="Add Forgejo Debian repository")
    def install_debian(owner: str = "", codename: str = "") -> str:
        return install.debian(owner=owner, codename=codename)

    return mcp
