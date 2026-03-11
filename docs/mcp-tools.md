# Forge MCP Tools Reference

This document describes all MCP tools exposed by the forge server. Every service method is automatically available as both a CLI command and an MCP tool. MCP tool names follow the pattern `{service}_{method}`.

## Prerequisites

Configure the Forgejo connection before using any tools:

```toml
# config.local.toml (gitignored — safe for tokens)
[forgejo]
url = "https://git.app.home.southroute.com"
token = "your-api-token"
```

Or via environment variables:
- `FORGE_FORGEJO__URL` — Forgejo instance URL
- `FORGE_FORGEJO__TOKEN` — API token

Or via 1Password:
```toml
[forgejo]
url = "https://git.app.home.southroute.com"
token_op_ref = "op://vault/item/field"
```

---

## Auth Tools

### `auth_status`
Check authentication status and display the logged-in user.

**Parameters:** none

**Returns:** Formatted user info (login, name, email, admin status)

**Example usage:**
```
auth_status()
→ "Logged in as bayne\nName: Brian Payne\nEmail: bwpayne@gmail.com\nAdmin: True"
```

### `auth_token`
Display the configured API token (masked for security).

**Parameters:** none

**Returns:** Masked token and its source (env var, config file, or 1Password)

---

## Repo Tools

### `repo_list`
List repositories for a user or the authenticated user.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `owner` | str | `""` | Username to list repos for. Empty = authenticated user |
| `limit` | int | `30` | Max results |
| `page` | int | `1` | Page number |

**Returns:** Table of repositories (name, description, stars, language)

### `repo_view`
View repository details. Infers owner/repo from git remote if omitted.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `owner` | str | `""` | Repository owner. Empty = infer from git remote |
| `repo` | str | `""` | Repository name. Empty = infer from git remote |

**Returns:** Detailed repository view (name, description, visibility, stars, forks, language, default branch, URL)

### `repo_create`
Create a new repository.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `name` | str | `""` | **Required.** Repository name |
| `description` | str | `""` | Repository description |
| `private` | bool | `False` | Make repository private |
| `org` | str | `""` | Create under this organization (otherwise personal) |

**Returns:** Created repo name and URL

### `repo_fork`
Fork a repository.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `owner` | str | `""` | Source repo owner. Empty = infer from git remote |
| `repo` | str | `""` | Source repo name. Empty = infer from git remote |
| `org` | str | `""` | Fork into this organization |

**Returns:** Forked repo name and URL

### `repo_delete`
Delete a repository.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `owner` | str | `""` | Repo owner. Empty = infer from git remote |
| `repo` | str | `""` | Repo name. Empty = infer from git remote |

**Returns:** Confirmation message

### `repo_search`
Search repositories.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `query` | str | `""` | **Required.** Search query |
| `limit` | int | `30` | Max results |

**Returns:** Table of matching repositories

---

## Issue Tools

### `issue_list`
List issues in a repository.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `owner` | str | `""` | Repo owner. Empty = infer from git remote |
| `repo` | str | `""` | Repo name. Empty = infer from git remote |
| `state` | str | `"open"` | Filter by state: `open`, `closed`, `all` |
| `labels` | str | `""` | Comma-separated label names to filter by |
| `milestone` | str | `""` | Filter by milestone name |
| `limit` | int | `30` | Max results |
| `page` | int | `1` | Page number |

**Returns:** Table of issues (#, title, state, author)

### `issue_view`
View issue details.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `number` | int | `0` | **Required.** Issue number |
| `owner` | str | `""` | Repo owner |
| `repo` | str | `""` | Repo name |

**Returns:** Detailed issue view (number, title, state, author, labels, assignees, body)

### `issue_create`
Create an issue.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `title` | str | `""` | **Required.** Issue title |
| `body` | str | `""` | Issue body/description |
| `labels` | str | `""` | Comma-separated label names |
| `assignees` | str | `""` | Comma-separated usernames |
| `milestone` | int | `0` | Milestone ID |
| `owner` | str | `""` | Repo owner |
| `repo` | str | `""` | Repo name |

**Returns:** Created issue number, title, and URL

### `issue_close`
Close an issue.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `number` | int | `0` | **Required.** Issue number |
| `owner` | str | `""` | Repo owner |
| `repo` | str | `""` | Repo name |

**Returns:** Confirmation message

### `issue_reopen`
Reopen a closed issue.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `number` | int | `0` | **Required.** Issue number |
| `owner` | str | `""` | Repo owner |
| `repo` | str | `""` | Repo name |

**Returns:** Confirmation message

### `issue_comment`
Add a comment to an issue.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `number` | int | `0` | **Required.** Issue number |
| `body` | str | `""` | **Required.** Comment body |
| `owner` | str | `""` | Repo owner |
| `repo` | str | `""` | Repo name |

**Returns:** Confirmation with comment URL

### `issue_edit`
Edit an issue's title and/or body.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `number` | int | `0` | **Required.** Issue number |
| `title` | str | `""` | New title (if provided) |
| `body` | str | `""` | New body (if provided) |
| `owner` | str | `""` | Repo owner |
| `repo` | str | `""` | Repo name |

**Returns:** Updated issue number and title

---

## Pull Request Tools

### `pr_list`
List pull requests.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `owner` | str | `""` | Repo owner |
| `repo` | str | `""` | Repo name |
| `state` | str | `"open"` | Filter: `open`, `closed`, `all` |
| `limit` | int | `30` | Max results |
| `page` | int | `1` | Page number |

**Returns:** Table of PRs (#, title, state, author)

### `pr_view`
View pull request details.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `number` | int | `0` | **Required.** PR number |
| `owner` | str | `""` | Repo owner |
| `repo` | str | `""` | Repo name |

**Returns:** Detailed PR view (number, title, state, author, head/base branches, mergeable, body)

### `pr_create`
Create a pull request.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `title` | str | `""` | **Required.** PR title |
| `body` | str | `""` | PR description |
| `head` | str | `""` | **Required.** Source branch |
| `base` | str | `"main"` | Target branch |
| `owner` | str | `""` | Repo owner |
| `repo` | str | `""` | Repo name |

**Returns:** Created PR number, title, and URL

### `pr_merge`
Merge a pull request.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `number` | int | `0` | **Required.** PR number |
| `method` | str | `"merge"` | Merge method: `merge`, `rebase`, or `squash` |
| `owner` | str | `""` | Repo owner |
| `repo` | str | `""` | Repo name |

**Returns:** Confirmation with merge method

### `pr_close`
Close a pull request without merging.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `number` | int | `0` | **Required.** PR number |
| `owner` | str | `""` | Repo owner |
| `repo` | str | `""` | Repo name |

**Returns:** Confirmation message

### `pr_reopen`
Reopen a closed pull request.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `number` | int | `0` | **Required.** PR number |
| `owner` | str | `""` | Repo owner |
| `repo` | str | `""` | Repo name |

**Returns:** Confirmation message

### `pr_diff`
View the diff of a pull request.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `number` | int | `0` | **Required.** PR number |
| `owner` | str | `""` | Repo owner |
| `repo` | str | `""` | Repo name |

**Returns:** Raw diff text

### `pr_review`
Submit a review on a pull request.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `number` | int | `0` | **Required.** PR number |
| `body` | str | `""` | Review comment |
| `event` | str | `"COMMENT"` | Review type: `APPROVE`, `REQUEST_CHANGES`, or `COMMENT` |
| `owner` | str | `""` | Repo owner |
| `repo` | str | `""` | Repo name |

**Returns:** Confirmation with review type and ID

---

## Release Tools

### `release_list`
List releases.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `owner` | str | `""` | Repo owner |
| `repo` | str | `""` | Repo name |
| `limit` | int | `30` | Max results |
| `page` | int | `1` | Page number |

**Returns:** Table of releases (tag, title, author, published date)

### `release_view`
View release details by tag.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `tag` | str | `""` | **Required.** Release tag (e.g. `v1.0.0`) |
| `owner` | str | `""` | Repo owner |
| `repo` | str | `""` | Repo name |

**Returns:** Detailed release view (name, tag, author, date, body, assets)

### `release_create`
Create a release.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `tag` | str | `""` | **Required.** Tag name (e.g. `v1.0.0`) |
| `title` | str | `""` | Release title (defaults to tag) |
| `body` | str | `""` | Release notes |
| `draft` | bool | `False` | Create as draft |
| `prerelease` | bool | `False` | Mark as prerelease |
| `owner` | str | `""` | Repo owner |
| `repo` | str | `""` | Repo name |

**Returns:** Created release name and URL

### `release_delete`
Delete a release by tag.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `tag` | str | `""` | **Required.** Release tag |
| `owner` | str | `""` | Repo owner |
| `repo` | str | `""` | Repo name |

**Returns:** Confirmation message

### `release_edit`
Edit a release.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `tag` | str | `""` | **Required.** Release tag |
| `title` | str | `""` | New title |
| `body` | str | `""` | New release notes |
| `draft` | bool | `False` | Draft status |
| `prerelease` | bool | `False` | Prerelease status |
| `owner` | str | `""` | Repo owner |
| `repo` | str | `""` | Repo name |

**Returns:** Updated release name

---

## Organization Tools

### `org_list`
List organizations the authenticated user belongs to.

**Parameters:** none

**Returns:** Table of organizations (name, description, visibility)

### `org_view`
View organization details.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `org` | str | `""` | **Required.** Organization name |

**Returns:** Detailed org view (name, description, visibility, location, website)

### `org_repos`
List repositories in an organization.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `org` | str | `""` | **Required.** Organization name |
| `limit` | int | `30` | Max results |
| `page` | int | `1` | Page number |

**Returns:** Table of repositories

### `org_members`
List members of an organization.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `org` | str | `""` | **Required.** Organization name |
| `limit` | int | `30` | Max results |
| `page` | int | `1` | Page number |

**Returns:** Table of members (username, name, email)

---

## Common Patterns for Agents

### Owner/Repo Inference
Most repo-scoped tools accept `owner` and `repo` parameters. When omitted (empty string), the tool automatically detects these from the current git working directory's `origin` remote URL. This means agents operating within a cloned repository can call tools without specifying owner/repo.

### Typical Workflows

**Create an issue and comment on it:**
```python
# Create
result = issue_create(title="Bug: login fails", body="Steps to reproduce...")
# → "Created issue #42: Bug: login fails\nhttps://..."

# Comment
issue_comment(number=42, body="Investigating this now")
```

**Create a PR and merge it:**
```python
# Create PR from feature branch
pr_create(title="Fix login bug", head="fix-login", base="main", body="Fixes #42")
# → "Created PR #10: Fix login bug\nhttps://..."

# After CI passes, merge via squash
pr_merge(number=10, method="squash")
# → "Merged PR #10 via squash"
```

**Search for repos and view details:**
```python
repo_search(query="forge", limit=5)
# → table of matching repos

repo_view(owner="bayne", repo="forge")
# → detailed repo info
```

**Check auth and list repos:**
```python
auth_status()
# → "Logged in as bayne..."

repo_list()
# → table of authenticated user's repos
```

### Error Handling
Tools return error strings (not exceptions) when required parameters are missing:
```python
issue_create()
# → "Error: --title is required."

pr_create(title="PR")
# → "Error: --head is required (source branch)."
```

API errors raise exceptions:
- `ForgejoNotFoundError` — 404 (repo/issue/PR not found)
- `ForgejoAuthError` — 401/403 (bad token or insufficient permissions)
- `ForgejoValidationError` — 422 (invalid input)
- `ForgejoAPIError` — other HTTP errors
