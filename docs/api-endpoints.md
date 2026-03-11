# Forgejo API Endpoints Reference

This document maps each forge CLI command / MCP tool to the underlying Forgejo API v1 endpoint it calls. The full Swagger specification is available in `swagger.v1.json` (Forgejo API v14.0.2 / Gitea 1.22.0).

**Base URL:** `{forgejo_url}/api/v1`

---

## Auth

| Command | Method | Endpoint | Swagger `operationId` | Description |
|---------|--------|----------|----------------------|-------------|
| `auth status` | GET | `/user` | `userGetCurrent` | Returns the authenticated user's profile (login, name, email, admin status) |

---

## Repositories

| Command | Method | Endpoint | Swagger `operationId` | Description |
|---------|--------|----------|----------------------|-------------|
| `repo list` | GET | `/users/{owner}/repos` | `userListRepos` | List repos for a specific user/org |
| `repo list` (no owner) | GET | `/user/repos` | `userCurrentListRepos` | List the authenticated user's repos |
| `repo view` | GET | `/repos/{owner}/{repo}` | `repoGet` | Get repository details |
| `repo create` | POST | `/user/repos` | `createCurrentUserRepo` | Create a personal repository |
| `repo create --org` | POST | `/orgs/{org}/repos` | `createOrgRepo` | Create a repository under an organization |
| `repo fork` | POST | `/repos/{owner}/{repo}/forks` | `createFork` | Fork a repository |
| `repo delete` | DELETE | `/repos/{owner}/{repo}` | `repoDelete` | Delete a repository |
| `repo search` | GET | `/repos/search` | `repoSearch` | Full-text search across repositories |

---

## Issues

| Command | Method | Endpoint | Swagger `operationId` | Description |
|---------|--------|----------|----------------------|-------------|
| `issue list` | GET | `/repos/{owner}/{repo}/issues` | `issueListIssues` | List issues with state/label/milestone filtering |
| `issue view` | GET | `/repos/{owner}/{repo}/issues/{index}` | `issueGetIssue` | Get a single issue by number |
| `issue create` | POST | `/repos/{owner}/{repo}/issues` | `issueCreateIssue` | Create an issue with optional labels, assignees, milestone |
| `issue close` | PATCH | `/repos/{owner}/{repo}/issues/{index}` | `issueEditIssue` | Close an issue (sets `state: closed`) |
| `issue reopen` | PATCH | `/repos/{owner}/{repo}/issues/{index}` | `issueEditIssue` | Reopen an issue (sets `state: open`) |
| `issue comment` | POST | `/repos/{owner}/{repo}/issues/{index}/comments` | `issueCreateComment` | Add a comment to an issue |
| `issue edit` | PATCH | `/repos/{owner}/{repo}/issues/{index}` | `issueEditIssue` | Edit an issue's title and/or body |

**Note:** Label resolution uses an extra call to `GET /repos/{owner}/{repo}/labels` (`issueListLabels`) to map label names to IDs.

---

## Pull Requests

| Command | Method | Endpoint | Swagger `operationId` | Description |
|---------|--------|----------|----------------------|-------------|
| `pr list` | GET | `/repos/{owner}/{repo}/pulls` | `repoListPullRequests` | List pull requests with state filtering |
| `pr view` | GET | `/repos/{owner}/{repo}/pulls/{index}` | `repoGetPullRequest` | Get a single PR by number |
| `pr create` | POST | `/repos/{owner}/{repo}/pulls` | `repoCreatePullRequest` | Create a PR with head/base branches |
| `pr merge` | POST | `/repos/{owner}/{repo}/pulls/{index}/merge` | `repoMergePullRequest` | Merge a PR (merge, rebase, or squash) |
| `pr close` | PATCH | `/repos/{owner}/{repo}/pulls/{index}` | `repoEditPullRequest` | Close a PR (sets `state: closed`) |
| `pr reopen` | PATCH | `/repos/{owner}/{repo}/pulls/{index}` | `repoEditPullRequest` | Reopen a PR (sets `state: open`) |
| `pr diff` | GET | `/repos/{owner}/{repo}/pulls/{index}.diff` | — | Raw diff output (not a JSON endpoint) |
| `pr review` | POST | `/repos/{owner}/{repo}/pulls/{index}/reviews` | `repoCreatePullReview` | Submit a review (APPROVE, REQUEST_CHANGES, COMMENT) |

---

## Releases

| Command | Method | Endpoint | Swagger `operationId` | Description |
|---------|--------|----------|----------------------|-------------|
| `release list` | GET | `/repos/{owner}/{repo}/releases` | `repoListReleases` | List releases with pagination |
| `release view` | GET | `/repos/{owner}/{repo}/releases/tags/{tag}` | `repoGetReleaseByTag` | Get a release by tag name |
| `release create` | POST | `/repos/{owner}/{repo}/releases` | `repoCreateRelease` | Create a release (supports draft/prerelease flags) |
| `release delete` | GET + DELETE | `/repos/{owner}/{repo}/releases/tags/{tag}` then `/repos/{owner}/{repo}/releases/{id}` | `repoGetReleaseByTag` + `repoDeleteRelease` | Resolve tag to ID, then delete |
| `release edit` | GET + PATCH | `/repos/{owner}/{repo}/releases/tags/{tag}` then `/repos/{owner}/{repo}/releases/{id}` | `repoGetReleaseByTag` + `repoEditRelease` | Resolve tag to ID, then update |

---

## Organizations

| Command | Method | Endpoint | Swagger `operationId` | Description |
|---------|--------|----------|----------------------|-------------|
| `org list` | GET | `/user/orgs` | `orgListCurrentUserOrgs` | List the authenticated user's organizations |
| `org view` | GET | `/orgs/{org}` | `orgGet` | Get organization details |
| `org repos` | GET | `/orgs/{org}/repos` | `orgListRepos` | List repositories in an organization |
| `org members` | GET | `/orgs/{org}/members` | `orgListMembers` | List members of an organization |

---

## Endpoints Not Yet Covered

The Forgejo API v1 exposes ~304 endpoints. The following categories are available in the API but not yet wrapped by forge:

| Category | Example Endpoints | Description |
|----------|-------------------|-------------|
| **Admin** | `/admin/users`, `/admin/orgs` | Server administration |
| **Notifications** | `/notifications`, `/repos/{owner}/{repo}/notifications` | Notification management |
| **Labels** | `/repos/{owner}/{repo}/labels` | Label CRUD (used internally for issue creation) |
| **Milestones** | `/repos/{owner}/{repo}/milestones` | Milestone management |
| **Teams** | `/orgs/{org}/teams`, `/teams/{id}` | Organization team management |
| **Webhooks** | `/repos/{owner}/{repo}/hooks` | Repository webhook management |
| **Git data** | `/repos/{owner}/{repo}/git/refs`, `/repos/{owner}/{repo}/git/trees` | Low-level git operations |
| **Branches** | `/repos/{owner}/{repo}/branches` | Branch management and protection |
| **Commits** | `/repos/{owner}/{repo}/git/commits` | Commit data and statuses |
| **Contents** | `/repos/{owner}/{repo}/contents` | File CRUD within repos |
| **Topics** | `/repos/{owner}/{repo}/topics` | Repository topic/tag management |
| **Stars/Watch** | `/user/starred`, `/repos/{owner}/{repo}/subscription` | Social features |
| **GPG/SSH keys** | `/user/gpg_keys`, `/user/keys` | Key management |
| **ActivityPub** | `/activitypub/*` | Federation endpoints |
| **Packages** | `/packages/{owner}` | Package registry |
