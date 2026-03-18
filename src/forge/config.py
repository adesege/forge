"""Configuration for forge.

Always loads from the XDG config directory (~/.config/forge/), never CWD.
"""

from __future__ import annotations

import os
import tomllib
from pathlib import Path
from typing import Any

APP_NAME = "forge"
ENV_PREFIX = "FORGE_"


def _xdg_config_dir() -> Path:
    """Return the XDG config directory for forge."""
    xdg_config_home = os.environ.get("XDG_CONFIG_HOME") or str(
        Path.home() / ".config"
    )
    return Path(xdg_config_home) / APP_NAME


def _load_toml(path: Path) -> dict[str, Any]:
    with open(path, "rb") as f:
        return tomllib.load(f)


def _deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    """Recursively merge override into base."""
    result = dict(base)
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    return result


def _apply_env_overrides(config: dict[str, Any], prefix: str) -> dict[str, Any]:
    """Apply environment variables as overrides.

    FORGE_SERVER__HOST=x  ->  config["server"]["host"] = "x"
    """
    result = dict(config)
    for key, value in os.environ.items():
        if not key.startswith(prefix):
            continue
        parts = key[len(prefix) :].lower().split("__")
        d = result
        for part in parts[:-1]:
            d = d.setdefault(part, {})
        d[parts[-1]] = value
    return result


def get_config(config_path: str | None = None) -> dict[str, Any]:
    """Load configuration from XDG config directory only.

    Loading order (later values win):
    1. ~/.config/forge/config.toml
    2. ~/.config/forge/config.local.toml
    3. Explicit config_path if provided
    4. Environment variables prefixed with FORGE_
    """
    merged: dict[str, Any] = {}

    xdg_dir = _xdg_config_dir()
    for name in ["config.toml", "config.local.toml"]:
        path = xdg_dir / name
        if path.exists():
            merged = _deep_merge(merged, _load_toml(path))

    if config_path:
        path = Path(config_path)
        if path.exists():
            merged = _deep_merge(merged, _load_toml(path))

    merged = _apply_env_overrides(merged, ENV_PREFIX)

    return merged
