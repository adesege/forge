# forge

forge — a click-clop project

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

