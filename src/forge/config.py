"""Configuration for forge."""

from __future__ import annotations

from pathlib import Path

from click_clop.config import load_config

_DEFAULT_CONFIG_PATH = Path.home() / ".config" / "forge" / "config.toml"


def get_config(config_path: str | None = None) -> dict:
    """Load the project configuration."""
    if config_path is None:
        config_path = str(_DEFAULT_CONFIG_PATH)
    return load_config(config_path, env_prefix="FORGE_")
