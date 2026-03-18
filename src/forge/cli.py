"""CLI entry point for forge."""

from __future__ import annotations

import click
from click_clop import expose_cli
from click_clop.config import load_config
from click_clop.logging import setup_logging

# Import service modules here so they auto-register, e.g.:
#   from forge.services import my_service  # noqa: F401


@click.group()
@click.version_option(prog_name="forge")
@click.option("--config", "config_path", default=None, help="Path to config.toml")
@click.option("--log-level", default="INFO", help="Log level")
@click.pass_context
def main(ctx: click.Context, config_path: str | None, log_level: str) -> None:
    """forge — a click-clop project"""
    ctx.ensure_object(dict)
    ctx.obj["config"] = load_config(config_path, env_prefix="FORGE_")
    setup_logging(level=log_level, json_output=False, service_name="forge")


# Auto-expose all registered services as CLI subcommands
expose_cli(main)


# ── Hybrid CLI pattern ───────────────────────────────────────────────────────
# If your project needs a primary interactive command (not a service method),
# use invoke_without_command=True on the group:
#
#   @click.group(invoke_without_command=True)
#   @click.pass_context
#   def main(ctx, ...):
#       if ctx.invoked_subcommand is None:
#           # Default interactive behaviour when no subcommand given
#           run_interactive(ctx.args)
#
#   expose_cli(main)  # Service subcommands still available
#
# This gives you both:
#   myapp                    -> runs interactive default
#   myapp my-service method  -> runs service subcommand
