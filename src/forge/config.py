"""TOML configuration loading with environment variable overlay."""

from __future__ import annotations

import os
import tomllib
from pathlib import Path
from typing import Any


def load_config(
    config_path: str | Path | None = None,
    env_prefix: str = "FORGE_",
    app_name: str | None = None,
) -> dict[str, Any]:
    """Load configuration from TOML files with environment variable overrides.

    Configuration is read only from trusted locations — never from the current
    working directory — so running forge inside an untrusted repository cannot
    override your Forgejo URL/token or inject environment variables into the
    subprocesses forge spawns.

    Loading order (later values win):
    1. XDG app config: ~/.config/{app_name}/config.toml (+ config.local.toml), when app_name is set
    2. Explicit config_path if provided
    3. Environment variables prefixed with env_prefix
    """
    merged: dict[str, Any] = {}

    if app_name:
        xdg_config_home = os.environ.get("XDG_CONFIG_HOME") or str(Path.home() / ".config")
        xdg_app_dir = Path(xdg_config_home) / app_name
        for name in ["config.toml", "config.local.toml"]:
            path = xdg_app_dir / name
            if path.exists():
                merged = _deep_merge(merged, _load_toml(path))

    if config_path:
        path = Path(config_path)
        if path.exists():
            merged = _deep_merge(merged, _load_toml(path))

    merged = _apply_env_overrides(merged, env_prefix)
    return merged


def _load_toml(path: Path) -> dict[str, Any]:
    with open(path, "rb") as f:
        return tomllib.load(f)


def _deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    result = dict(base)
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    return result


def _apply_env_overrides(config: dict[str, Any], prefix: str) -> dict[str, Any]:
    result = dict(config)
    for key, value in os.environ.items():
        if not key.startswith(prefix):
            continue
        parts = key[len(prefix) :].lower().split("__")
        _set_nested(result, parts, value)
    return result


def _set_nested(d: dict[str, Any], keys: list[str], value: str) -> None:
    for key in keys[:-1]:
        d = d.setdefault(key, {})
    d[keys[-1]] = value
