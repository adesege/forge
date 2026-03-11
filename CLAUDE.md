# forge — Claude Code Guidelines

## Project Overview

forge — a click-clop project

Built with the **click-clop** framework.

Every feature is simultaneously a CLI command (Click) and MCP tool (FastMCP) via the service-layer pattern.


## Architecture

```

CLI (Click) ──┐
MCP (FastMCP) ─┘──> Service Layer (plain functions) ──> Config / Secrets


```

- **Services** live in `src/forge/services/`. Each service is a class with public methods.
- **CLI** is auto-generated from services in `cli.py` via `expose_cli()`.

- **MCP** are auto-generated in `server.py` via `expose_mcp()`.

- **Config** is loaded from `config.toml` with env var overrides (`FORGE_*`).

- **Secrets** are managed via 1Password (`op` CLI).



## Directory Structure

```
src/forge/
├── cli.py          # Click CLI entry point (auto-exposes services)

├── server.py       # MCP server (auto-exposes services)

├── config.py       # Config loader

├── secrets.py      # 1Password service

└── services/       # Business logic goes here
    ├── hello.py    # Example service
    └── ...         # Add new services here

tests/
├── conftest.py     # Shared fixtures
└── unit/           # Unit tests


features/           # Gherkin BDD tests
├── steps/          # Step definitions
└── *.feature       # Feature files



docs/               # Sphinx documentation




.forgejo/workflows/ # CI/CD pipelines

```

## Development Workflow

| Task | Command |
|------|---------|
| Install deps | `make install` |
| Install with dev deps | `make install-dev` |
| Run CLI | `uv run forge --help` |

| Run tests | `make test` |

| Run BDD tests | `make test-bdd` |

| Lint | `make lint` |
| Format | `make format` |

| Build docs | `make docs` |



| Build .deb | `make build-deb` |



| Publish PyPI | `make publish-pypi` |


| Publish .deb | `make publish-deb` |



## Adding a New Feature

1. Create a new service in `src/forge/services/your_feature.py`:
   ```python
   from click_clop.service import Service

   class YourFeatureService(Service):
       name = "your-feature"
       description = "What it does"

       def your_method(self, arg: str) -> str:
           """Method docstring becomes help text."""
           return f"Result: {arg}"

   _service = YourFeatureService()
   ```

2. Import it in `src/forge/services/__init__.py`

3. It's now automatically available as:
   - CLI: `forge your-feature your-method --arg value`

   - MCP: tool `your-feature_your_method`



4. Write tests in `tests/unit/test_your_feature.py`


5. Write a `.feature` file in `features/your_feature.feature`


## Agent Rules

When implementing changes:

1. **Use worktrees**: Use Claude Code's built-in `EnterWorktree` to work in isolation. Never commit directly to main — always work in a worktree branch.
2. **Commit changes** in the worktree branch using the conventional commit format below
3. **Update documentation** if the change affects public APIs
4. **Write tests**: unit tests in `tests/unit/` and `.feature` files in `features/`

5. **Follow the service pattern**: business logic in services, not in CLI/MCP layers
6. **If CLI-focused**: create a quick asciinema demo with `make demo`

### Commit Message Format

Follow **Conventional Commits** strictly. A `commit-msg` hook enforces this format:

```
<type>(<scope>): <description>
```

- **Types**: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`, `ci`, `perf`, `build`
- **Scope**: optional, describes the area of change (e.g., `api`, `cli`, `helm`)
- **Description**: imperative mood, lowercase, no period at end, max 72 chars
  - "add feature" not "added feature"
  - "fix bug" not "fixes bug"
- **Body** (optional): explain the "why", not the "what"
- **Footer** (optional): `BREAKING CHANGE:`, `Closes #123`, `Co-authored-by:`

Examples:
```
feat: add user authentication
fix(api): handle null response
docs: update README with setup instructions
```

The commit template is at `.git-templates/commit-message.txt` — install hooks with `make hooks`.


### Build Verification Checklist

Before pushing or tagging a release, agents MUST verify:

- [ ] `make lint` passes (ruff + mypy)
- [ ] `make test` passes (all unit tests green)

- [ ] `make test-bdd` passes (all BDD scenarios green)

- [ ] `make build` succeeds (wheel builds cleanly)


- [ ] `make build-deb` succeeds (Debian package builds without errors)


### Publishing Workflow

To publish a release:
1. Ensure all checks above pass
2. Update version in `pyproject.toml` if not using tag-based versioning
3. Create and push a semver tag: `git tag v<VERSION> && git push origin v<VERSION>`
4. Forgejo Actions will automatically build and publish to all configured registries



## CI/CD & Publishing

This project uses **Forgejo Actions** for CI/CD. Workflows are in `.forgejo/workflows/`.

| Workflow | Trigger | Purpose |
|----------|---------|---------|
| `ci.yml` | Push/PR to main | Lint, type-check, test |
| `publish-package.yml` | Tag `v*` | Build + publish to Forgejo PyPI |


| `publish-deb.yml` | Tag `v*` | Build + upload .deb to Forgejo Debian registry |


**Registry URLs** (Forgejo at `git.app.home.southroute.com`):
- PyPI: `https://git.app.home.southroute.com/api/packages/bayne/pypi`


- Debian: `https://git.app.home.southroute.com/api/packages/bayne/debian`


**Authentication**: Workflows use the automatic `github.token` provided by Forgejo Actions — no manual secret setup required. For local `make publish-*` commands, `FORGEJO_TOKEN` is resolved automatically via `dcaf3a0766e9b9ff42d7461e9d415045c61dc266`. Override with `make publish-pypi FORGEJO_TOKEN=<token>` if needed.


## Git Conventions

- Hooks are in `.git-hooks/` — install with `make hooks`
- Commit message format: Conventional Commits
- Template: `.git-templates/commit-message.txt`

## Config

- `config.toml` — base config
- `config.dev.toml` — development overrides
- `config.local.toml` — local overrides (gitignored)
- Environment variables: `FORGE_<SECTION>__<KEY>=value`


## Installing from Forgejo

```bash
# Python package
pip install forge --index-url https://git.app.home.southroute.com/api/packages/bayne/pypi/simple/



# Debian package
echo "deb https://git.app.home.southroute.com/api/packages/bayne/debian trixie main" | sudo tee /etc/apt/sources.list.d/forgejo.list
sudo apt-get update && sudo apt-get install forge

```

