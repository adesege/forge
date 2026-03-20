"""TOML configuration loading with environment variable overlay."""

from __future__ import annotations

import os
import tomllib
from pathlib import Path
from typing import Any

_DEFAULT_CONFIG_FILES = ["config.toml", "config.dev.toml", "config.local.toml"]
_DEFAULT_ENV_FILES = [".env"]


def load_config(
    config_path: str | Path | None = None,
    env_prefix: str = "FORGE_",
    app_name: str | None = None,
) -> dict[str, Any]:
    """Load configuration from TOML files with environment variable overrides.

    Loading order (later values win):
    1. config.toml / config.dev.toml / config.local.toml (CWD defaults)
    2. XDG app config: ~/.config/{app_name}/config.toml (when app_name is set)
    3. Explicit config_path if provided
    4. Environment variables prefixed with env_prefix
    """
    merged: dict[str, Any] = {}

    for name in _DEFAULT_ENV_FILES:
        path = Path(name)
        if path.exists():
            _load_env_file(path)

    for name in _DEFAULT_CONFIG_FILES:
        path = Path(name)
        if path.exists():
            merged = _deep_merge(merged, _load_toml(path))

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


def _load_env_file(path: Path) -> None:
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if line.startswith("export "):
                line = line[7:]
            key, _, value = line.partition("=")
            key = key.strip()
            if not key or not _:
                continue
            value = value.strip()
            if len(value) >= 2 and value[0] == value[-1] and value[0] in ("'", '"'):
                value = value[1:-1]
            if key not in os.environ:
                os.environ[key] = value
