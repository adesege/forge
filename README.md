# forge

A CLI and MCP server for [Forgejo](https://forgejo.org) instances. Every command is available both as a CLI command and as an MCP tool, powered by the service-layer pattern.

forge auto-detects repository context from your git remote, so most commands work without specifying `--owner` or `--repo` when run inside a git repository.

## Installation

forge installs straight from source with [uv](https://docs.astral.sh/uv/) — no package registry, pinned to a tag you control:

```bash
uv tool install "git+https://github.com/adesege/forge.git@v2.4.0"
```

Update by re-running with a newer tag. Prefer `pipx`? `pipx install "git+https://github.com/adesege/forge.git@v2.4.0"`. Requires Python 3.14+.

## Setup

Configure your Forgejo instance URL and authentication token:

```toml
# ~/.config/forge/config.toml
[forgejo]
url = "https://git.example.com"
token = "your-token-here"
# Or resolve the token from 1Password instead of storing it:
# token_op_ref = "op://Dev/Forgejo/token"
default_owner = "my-org"
```

The token can also come from the environment (`FORGE_FORGEJO__TOKEN`). Verify the connection:

```bash
forge auth status
```

## Commands

### Authentication

| Command | Description |
|---------|-------------|
| `forge auth status` | Check authentication status and display the logged-in user |
| `forge auth token` | Display the configured API token (masked) |

### Repositories

| Command | Description |
|---------|-------------|
| `forge repo list` | List repositories for a user/org or the authenticated user |
| `forge repo view` | View repository details (auto-detected from git remote) |
| `forge repo create` | Create a new repository and configure the git remote |
| `forge repo clone` | Clone a repository (interactive selector if name omitted) |
| `forge repo fork` | Fork a repository |
| `forge repo delete` | Delete a repository |
| `forge repo search` | Search repositories by keyword |

Options like `--owner`, `--repo`, `--limit`, `--page`, `--private`, `--org`, and `--description` are available where applicable.

### Issues

| Command | Description |
|---------|-------------|
| `forge issue list` | List issues (filterable by `--state`, `--labels`, `--milestone`) |
| `forge issue view NUMBER` | View issue details |
| `forge issue create` | Create an issue with `--title`, `--body`, `--labels`, `--assignees` |
| `forge issue edit NUMBER` | Edit an issue's title and/or body |
| `forge issue close NUMBER` | Close an issue |
| `forge issue reopen NUMBER` | Reopen a closed issue |
| `forge issue comment NUMBER` | Add a comment to an issue |

Labels can be specified by name (comma-separated) -- forge resolves them to IDs automatically.

### Pull Requests

| Command | Description |
|---------|-------------|
| `forge pr list` | List pull requests (filterable by `--state`) |
| `forge pr view NUMBER` | View pull request details |
| `forge pr create` | Create a PR with `--title`, `--body`, `--head`, `--base` |
| `forge pr merge NUMBER` | Merge a PR (`--method`: merge, rebase, or squash) |
| `forge pr close NUMBER` | Close a pull request |
| `forge pr reopen NUMBER` | Reopen a closed pull request |
| `forge pr diff NUMBER` | View the raw diff of a pull request |
| `forge pr checks NUMBER` | View CI check status, step details, and failure logs |
| `forge pr review NUMBER` | Submit a review (`--event`: APPROVE, REQUEST_CHANGES, COMMENT) |
| `forge pr react COMMENT_ID` | Add a reaction to a PR comment (+1, -1, heart, rocket, etc.) |

When listing PRs with only `--owner`, forge aggregates results across all of that user's repositories.

### CI / Actions

| Command | Description |
|---------|-------------|
| `forge ci runs` | List action runs (filterable by `--status` and `--event`) |
| `forge ci view RUN_ID` | View action run details |
| `forge ci log RUN_ID` | Get log output for a CI run job (`--job` selects which job) |
| `forge ci status` | Get commit statuses for a ref (branch, tag, or commit SHA) |

### Releases

| Command | Description |
|---------|-------------|
| `forge release list` | List releases |
| `forge release view TAG` | View release details by tag |
| `forge release create TAG` | Create a release (`--draft`, `--prerelease`) |
| `forge release edit TAG` | Edit a release |
| `forge release delete TAG` | Delete a release |

### Organizations

| Command | Description |
|---------|-------------|
| `forge org list` | List organizations the authenticated user belongs to |
| `forge org view ORG` | View organization details |
| `forge org repos ORG` | List repositories in an organization |
| `forge org members ORG` | List members of an organization |

### Packages

| Command | Description |
|---------|-------------|
| `forge package list` | List packages (filterable by `--type`: generic, pypi, npm, debian) |
| `forge package view` | View package version details |
| `forge package files` | List files in a package version |
| `forge package delete` | Delete a package version |
| `forge package publish` | Publish to the generic package registry |
| `forge package publish-deb` | Publish a `.deb` package (`--distribution`, `--component`) |
| `forge package publish-crate` | Publish a Rust `.crate` file |
| `forge package download` | Download a file from the generic package registry |

### Repository Configuration

| Command | Description |
|---------|-------------|
| `forge install pypi` | Add a Forgejo PyPI index to uv's global config |
| `forge install debian` | Add a Forgejo Debian repository to apt sources |

### Shell Completion

```bash
# Generate and install shell completions
forge completion bash  # Bash
forge completion zsh   # Zsh
forge completion fish  # Fish
```

### Global Options

| Option | Description |
|--------|-------------|
| `--config PATH` | Path to a config file |
| `--log-level LEVEL` | Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL) |
| `--version` | Display version |
| `--help` | Show help for any command |

## MCP Server

forge exposes its service layer as MCP tools via [FastMCP](https://github.com/jlowin/fastmcp), so AI assistants and automation that speak the Model Context Protocol can drive it. Each service maps 1:1 to a tool (e.g. `forge pr list` becomes the `pr_list` tool), defined in `src/forge/server.py`.

## Context Detection

When run inside a git repository, forge automatically detects:

- **Owner and repo** from the git remote URL (SSH, HTTPS, or SSH-scheme)
- **Forgejo remote** by matching the configured instance hostname against your remotes
- **Default owner** from config when `--owner` is omitted outside a repo

If multiple remotes match, forge prompts you to select one and caches the choice in `.git/config`.

## Configuration

forge reads configuration only from trusted locations — **never** from the current working directory — so running it inside an untrusted repository can't override your Forgejo URL/token or inject environment variables into the subprocesses forge spawns.

Sources are merged in order, with later values winning:

1. **`~/.config/forge/config.toml`** -- user-wide defaults (XDG config)
2. **`~/.config/forge/config.local.toml`** -- user-wide local overrides (XDG config)
3. **Explicit `--config` path** -- if passed via the CLI
4. **Environment variables** -- `FORGE_<SECTION>__<KEY>=value` (highest priority)

### Config Section

```toml
[forgejo]
url = "https://git.example.com"
token = "your-token-here"
# OR resolve from 1Password (requires the `op` CLI):
# token_op_ref = "op://Dev/Forgejo/token"
default_owner = "my-org"
```

### Environment Variable Overrides

Environment variables use the prefix `FORGE_` with double underscores (`__`) as section separators:

| Config key | Environment variable |
|------------|---------------------|
| `[forgejo] url` | `FORGE_FORGEJO__URL` |
| `[forgejo] token` | `FORGE_FORGEJO__TOKEN` |
| `[forgejo] default_owner` | `FORGE_FORGEJO__DEFAULT_OWNER` |

## Architecture

```
CLI (Click) ──┐
MCP (FastMCP) ─┘──> Service Layer (plain functions) ──> Config
```

Business logic lives in `src/forge/services/` as plain functions. CLI commands (`cli.py`) and MCP tools (`server.py`) are thin wrappers around these services.

## Development

```bash
make install-dev    # Install with dev dependencies (uv)
make test           # Run all unit tests
make test-bdd       # Run BDD feature tests
make lint           # Lint (ruff + mypy)
make format         # Format code
make docs           # Build Sphinx documentation
make build          # Build wheel
```

See `CLAUDE.md` for the full development guide.

## License

MIT
