"""Tests for the configuration loader."""

from __future__ import annotations

import os
from pathlib import Path
from unittest.mock import patch

from forge.config import (
    _apply_env_overrides,
    _deep_merge,
    _load_env_file,
    _set_nested,
    load_config,
)


class TestDeepMerge:
    """Tests for _deep_merge."""

    def test_basic_merge(self) -> None:
        base = {"a": 1, "b": 2}
        override = {"b": 3, "c": 4}
        result = _deep_merge(base, override)
        assert result == {"a": 1, "b": 3, "c": 4}

    def test_nested_merge(self) -> None:
        base = {"section": {"key1": "val1", "key2": "val2"}}
        override = {"section": {"key2": "new", "key3": "val3"}}
        result = _deep_merge(base, override)
        assert result == {"section": {"key1": "val1", "key2": "new", "key3": "val3"}}

    def test_override_replaces_non_dict(self) -> None:
        base = {"a": "string"}
        override = {"a": {"nested": True}}
        result = _deep_merge(base, override)
        assert result == {"a": {"nested": True}}

    def test_empty_base(self) -> None:
        result = _deep_merge({}, {"key": "val"})
        assert result == {"key": "val"}


class TestSetNested:
    """Tests for _set_nested."""

    def test_single_key(self) -> None:
        d: dict[str, object] = {}
        _set_nested(d, ["key"], "value")
        assert d == {"key": "value"}

    def test_nested_key(self) -> None:
        d: dict[str, object] = {}
        _set_nested(d, ["section", "key"], "value")
        assert d == {"section": {"key": "value"}}

    def test_creates_intermediate_dicts(self) -> None:
        d: dict[str, object] = {}
        _set_nested(d, ["a", "b", "c"], "deep")
        assert d == {"a": {"b": {"c": "deep"}}}


class TestApplyEnvOverrides:
    """Tests for _apply_env_overrides."""

    def test_applies_env_vars_with_prefix(self) -> None:
        with patch.dict("os.environ", {"FORGE_FORGEJO__TOKEN": "mytoken"}, clear=False):
            result = _apply_env_overrides({}, "FORGE_")
            assert result["forgejo"]["token"] == "mytoken"

    def test_ignores_non_prefixed_vars(self) -> None:
        with patch.dict("os.environ", {"OTHER_VAR": "ignored"}, clear=False):
            result = _apply_env_overrides({}, "FORGE_")
            assert "other" not in result


class TestLoadEnvFile:
    """Tests for _load_env_file."""

    def test_loads_env_file(self, tmp_path: Path) -> None:
        env_file = tmp_path / ".env"
        env_file.write_text('TEST_FORGE_CONFIG_VAR="hello"\n')
        with patch.dict("os.environ", {}, clear=False):
            os.environ.pop("TEST_FORGE_CONFIG_VAR", None)
            _load_env_file(env_file)
            assert os.environ.get("TEST_FORGE_CONFIG_VAR") == "hello"
            del os.environ["TEST_FORGE_CONFIG_VAR"]

    def test_skips_comments(self, tmp_path: Path) -> None:
        env_file = tmp_path / ".env"
        env_file.write_text("# this is a comment\n")
        _load_env_file(env_file)

    def test_skips_empty_lines(self, tmp_path: Path) -> None:
        env_file = tmp_path / ".env"
        env_file.write_text("\n\n\n")
        _load_env_file(env_file)

    def test_handles_export_prefix(self, tmp_path: Path) -> None:
        env_file = tmp_path / ".env"
        env_file.write_text("export TEST_FORGE_EXPORT_VAR=world\n")
        with patch.dict("os.environ", {}, clear=False):
            os.environ.pop("TEST_FORGE_EXPORT_VAR", None)
            _load_env_file(env_file)
            assert os.environ.get("TEST_FORGE_EXPORT_VAR") == "world"
            del os.environ["TEST_FORGE_EXPORT_VAR"]

    def test_single_quoted_values(self, tmp_path: Path) -> None:
        env_file = tmp_path / ".env"
        env_file.write_text("TEST_FORGE_QUOTE_VAR='quoted'\n")
        with patch.dict("os.environ", {}, clear=False):
            os.environ.pop("TEST_FORGE_QUOTE_VAR", None)
            _load_env_file(env_file)
            assert os.environ.get("TEST_FORGE_QUOTE_VAR") == "quoted"
            del os.environ["TEST_FORGE_QUOTE_VAR"]

    def test_existing_env_not_overwritten(self, tmp_path: Path) -> None:
        env_file = tmp_path / ".env"
        env_file.write_text("TEST_FORGE_EXIST_VAR=new\n")
        with patch.dict("os.environ", {"TEST_FORGE_EXIST_VAR": "existing"}, clear=False):
            _load_env_file(env_file)
            assert os.environ["TEST_FORGE_EXIST_VAR"] == "existing"

    def test_skips_lines_without_equals(self, tmp_path: Path) -> None:
        env_file = tmp_path / ".env"
        env_file.write_text("NOEQUALSSIGN\n")
        _load_env_file(env_file)


class TestLoadConfig:
    """Tests for the main load_config function."""

    def test_loads_from_toml_file(self, tmp_path: Path) -> None:
        config_file = tmp_path / "config.toml"
        config_file.write_text('[forgejo]\nurl = "https://git.example.com"\n')
        result = load_config(config_path=str(config_file))
        assert result["forgejo"]["url"] == "https://git.example.com"

    def test_env_overrides_config(self, tmp_path: Path) -> None:
        config_file = tmp_path / "config.toml"
        config_file.write_text('[forgejo]\nurl = "https://original.com"\n')
        with patch.dict("os.environ", {"FORGE_FORGEJO__URL": "https://override.com"}, clear=False):
            result = load_config(config_path=str(config_file))
            assert result["forgejo"]["url"] == "https://override.com"

    def test_xdg_config(self, tmp_path: Path) -> None:
        xdg_dir = tmp_path / "xdg" / "forge"
        xdg_dir.mkdir(parents=True)
        (xdg_dir / "config.toml").write_text('[forgejo]\nurl = "https://xdg.example.com"\n')
        with patch.dict("os.environ", {"XDG_CONFIG_HOME": str(tmp_path / "xdg")}, clear=False):
            result = load_config(app_name="forge")
            assert result["forgejo"]["url"] == "https://xdg.example.com"

    def test_missing_config_path_ignored(self) -> None:
        result = load_config(config_path="/nonexistent/config.toml")
        assert isinstance(result, dict)
