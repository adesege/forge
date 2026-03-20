"""CLI entry point for forge."""

from __future__ import annotations

import logging
import sys

import click
import structlog
from click_clop import expose_cli

from forge.config import load_config


def setup_logging(level: str = "INFO", service_name: str = "") -> None:
    """Configure structured logging."""
    log_level = getattr(logging, level.upper(), logging.INFO)

    shared_processors: list[structlog.types.Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.UnicodeDecoder(),
    ]

    structlog.configure(
        processors=[
            *shared_processors,
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    formatter = structlog.stdlib.ProcessorFormatter(
        processors=[
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            structlog.dev.ConsoleRenderer(),
        ],
    )

    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.addHandler(handler)
    root_logger.setLevel(log_level)

    if service_name:
        structlog.contextvars.bind_contextvars(service=service_name)


@click.group()
@click.version_option(prog_name="forge")
@click.option("--config", "config_path", default=None, help="Path to config.toml")
@click.option("--log-level", default="INFO", help="Log level")
@click.pass_context
def main(ctx: click.Context, config_path: str | None, log_level: str) -> None:
    """A click-clop CLI application"""
    ctx.ensure_object(dict)
    ctx.obj["config"] = load_config(config_path, env_prefix="FORGE_", app_name="forge")
    setup_logging(level=log_level, service_name="forge")


# ── Register service commands ────────────────────────────────────────────────
# Explicitly import service modules to trigger registration, then expose as CLI.
from forge.services import auth as _auth  # noqa: F401, E402
from forge.services import completion as _completion  # noqa: F401, E402
from forge.services import install as _install  # noqa: F401, E402
from forge.services import issue as _issue  # noqa: F401, E402
from forge.services import org as _org  # noqa: F401, E402
from forge.services import package as _package  # noqa: F401, E402
from forge.services import pr as _pr  # noqa: F401, E402
from forge.services import release as _release  # noqa: F401, E402
from forge.services import repo as _repo  # noqa: F401, E402

expose_cli(main)
