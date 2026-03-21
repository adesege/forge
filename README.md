# forge

A click-clop CLI application

Built with click-clop — every feature is simultaneously a CLI command and MCP tool.

## Quick Start

```bash
make install-dev
make test
uv run forge --help
```

## Development

```bash
make install-dev    # Install with dev dependencies
make test           # Run all tests

make test-bdd       # Run BDD feature tests

make lint           # Lint code
make format         # Format code


make docs           # Build documentation



make build-deb      # Build Debian package


```

## Architecture

```

CLI (Click) ──┐
MCP (FastMCP) ─┘──> Service Layer ──> Config / Secrets


```

Add new features as services in `src/forge/services/`. They're automatically exposed
across both interfaces. See `CLAUDE.md` for full development guide.


## Configuration

forge loads configuration from TOML files with environment variable overrides. Files are
loaded in order, with later values winning (deep-merged):

1. **`config.toml`** — base/default configuration (checked into the repo)
2. **`config.dev.toml`** — development overrides (checked into the repo)
3. **`config.local.toml`** — local/personal overrides (gitignored)
4. **`~/.config/forge/config.toml`** — user-wide defaults (XDG config)
5. **`~/.config/forge/config.local.toml`** — user-wide local overrides (XDG config)
6. **Explicit `--config` path** — if passed via the CLI (`forge --config /path/to/file.toml`)
7. **Environment variables** — `FORGE_<SECTION>__<KEY>=value` (highest priority)

A `.env` file in the current directory is also loaded (if present) before config files,
but existing environment variables are never overwritten by `.env` values.

### Config Sections

```toml
[server]
host = "0.0.0.0"
port = 8000

[logging]
level = "INFO"          # DEBUG, INFO, WARNING, ERROR, CRITICAL
json_output = true

[telemetry]
enabled = true
otlp_endpoint = "http://localhost:4317"

[onepassword]
vault = ""

[forgejo]
url = "https://git.example.com"
token = "your-token-here"
# OR use a command for dynamic retrieval:
# token_cmd = 'op read "op://Dev/Forgejo/token"'
default_owner = "my-org"
```

### Environment Variable Overrides

Environment variables use the prefix `FORGE_` with double underscores (`__`) as section
separators. For example:

| Config key | Environment variable |
|------------|---------------------|
| `[server] port` | `FORGE_SERVER__PORT` |
| `[logging] level` | `FORGE_LOGGING__LEVEL` |
| `[forgejo] url` | `FORGE_FORGEJO__URL` |
| `[forgejo] token` | `FORGE_FORGEJO__TOKEN` |

### Recommended Setup

- Put shared defaults in `config.toml` (committed)
- Put development overrides in `config.dev.toml` (committed)
- Put secrets and personal settings in `config.local.toml` (gitignored)
- For settings shared across multiple projects, use `~/.config/forge/config.toml`

## Publishing

This project publishes to Forgejo at `git.app.home.southroute.com` via CI/CD on tagged releases.

```bash
git tag v0.1.0
git push origin v0.1.0
```

### Install from Forgejo

```bash
# Python package
pip install forge --index-url https://git.app.home.southroute.com/api/packages/southroute/pypi/simple/



# Debian package (add repo first)
echo "deb https://git.app.home.southroute.com/api/packages/southroute/debian trixie main" | sudo tee /etc/apt/sources.list.d/forgejo.list
sudo apt-get update && sudo apt-get install forge

```

