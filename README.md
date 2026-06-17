# forge

A fast, self-contained CLI for [Forgejo](https://forgejo.org) — manage repos, issues, pull requests, CI runs, releases, organizations, and packages from your terminal. The same service layer is also exposed as MCP tools for AI assistants.

forge auto-detects the owner and repo from your git remote, so most commands just work inside a repository.

## Install

forge installs straight from source with [uv](https://docs.astral.sh/uv/) — no package registry, pinned to a tag you control:

```bash
uv tool install "git+https://github.com/adesege/forge.git@v2.4.0"
```

Update by re-running with a newer tag. Prefer `pipx`? `pipx install "git+https://github.com/adesege/forge.git@v2.4.0"`.

Requires Python 3.14+.

## Setup

Configure your instance in `~/.config/forge/config.toml`:

```toml
[forgejo]
url = "https://git.example.com"
token = "your-token"
default_owner = "my-org"
```

Or pass the token via the environment: `FORGE_FORGEJO__TOKEN=...`. Then verify:

```bash
forge auth status
```

## Commands

Run `forge <group> --help` for the full set of subcommands and flags.

| Group | What it does |
|-------|--------------|
| `forge auth` | Check authentication and show the configured token (masked) |
| `forge repo` | List, view, create, clone, fork, search, and delete repositories |
| `forge issue` | Create, view, edit, comment on, and close/reopen issues |
| `forge pr` | Create, view, merge, review, diff, and inspect CI checks on pull requests |
| `forge ci` | List action runs, view details, fetch job logs, and read commit statuses |
| `forge release` | List, view, create, edit, and delete releases |
| `forge org` | View organizations, their repositories, and members |
| `forge package` | List, view, publish (generic / deb / crate), and download packages |
| `forge install` | Wire a Forgejo PyPI index or Debian repo into your local tooling |
| `forge completion` | Generate shell completions (`bash`, `zsh`, `fish`) |

Global options: `--config PATH`, `--log-level LEVEL`, `--version`, `--help`.

## Configuration

forge reads configuration only from trusted locations — **never** from the current working directory — so running it inside an untrusted repository can't redirect your token or leak it into spawned processes.

Sources, later winning:

1. `~/.config/forge/config.toml` then `config.local.toml` (XDG)
2. An explicit `--config PATH`
3. `FORGE_<SECTION>__<KEY>` environment variables (e.g. `FORGE_FORGEJO__URL`, `FORGE_FORGEJO__TOKEN`)

## Context detection

Inside a git repository, forge resolves the owner/repo from the remote URL (SSH, HTTPS, or `ssh://`) and matches your configured instance hostname. If several remotes match it asks once and caches the choice in `.git/config`. Outside a repo it falls back to `[forgejo].default_owner`.

## MCP server

The service layer is also published as MCP tools via [FastMCP](https://github.com/jlowin/fastmcp), so AI assistants can drive forge over the Model Context Protocol. Every service maps 1:1 to a tool (e.g. `pr_list`).

## Development

```bash
make install-dev   # install with dev dependencies (uv)
make test          # unit tests
make lint          # ruff + mypy
make format        # format
```

Architecture: business logic lives in `src/forge/services/` as plain functions; the CLI (`cli.py`) and MCP server (`server.py`) are thin wrappers over it.

## License

MIT
