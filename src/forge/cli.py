"""CLI entry point for forge."""

from __future__ import annotations

import click
from click_clop import expose_cli
from click_clop.logging import setup_logging

from forge.config import get_config

# Import services so they auto-register
from forge.services import (
    auth,  # noqa: F401
    completion,  # noqa: F401
    issue,  # noqa: F401
    org,  # noqa: F401
    pr,  # noqa: F401
    release,  # noqa: F401
    repo,  # noqa: F401
)


@click.group()
@click.version_option(prog_name="forge")
@click.option("--config", "config_path", default=None, help="Path to config.toml")
@click.option("--log-level", default="INFO", help="Log level")
@click.pass_context
def main(ctx: click.Context, config_path: str | None, log_level: str) -> None:
    """forge — a click-clop project"""
    ctx.ensure_object(dict)
    ctx.obj["config"] = get_config(config_path)
    setup_logging(level=log_level, json_output=False, service_name="forge")


# Auto-expose all registered services as CLI subcommands
expose_cli(main)
