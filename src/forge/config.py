"""Configuration for forge."""

from __future__ import annotations

from typing import Any

from click_clop.config import load_config


def get_config(config_path: str | None = None) -> dict[str, Any]:
    """Load the project configuration."""
    return load_config(config_path, env_prefix="FORGE_")
