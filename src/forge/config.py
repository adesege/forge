"""Configuration for forge."""

from __future__ import annotations

from click_clop.config import load_config


def get_config(config_path: str | None = None) -> dict:
    """Load the project configuration."""
    return load_config(config_path, env_prefix="FORGE_")
