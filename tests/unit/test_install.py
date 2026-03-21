"""Tests for the install service."""

from __future__ import annotations

import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

from forge.services.install import (
    InstallService,
    _get_forgejo_config,
    _get_forgejo_token,
    _get_forgejo_url,
    _get_os_release,
    _get_package_owner,
    _serialize_toml,
)


class TestHelperFunctions:
    """Tests for install service helper functions."""

    def test_get_forgejo_config(self) -> None:
        with patch(
            "forge.services.install.load_config",
            return_value={"forgejo": {"url": "https://git.example.com", "token": "tok"}},
        ):
            cfg = _get_forgejo_config()
            assert cfg["url"] == "https://git.example.com"
            assert cfg["token"] == "tok"

    def test_get_forgejo_config_empty(self) -> None:
        with patch("forge.services.install.load_config", return_value={}):
            cfg = _get_forgejo_config()
            assert cfg == {}

    def test_get_forgejo_url_from_config(self) -> None:
        with patch(
            "forge.services.install.load_config",
            return_value={"forgejo": {"url": "https://custom.example.com"}},
        ):
            assert _get_forgejo_url() == "https://custom.example.com"

    def test_get_forgejo_url_default(self) -> None:
        with patch("forge.services.install.load_config", return_value={}):
            assert "southroute" in _get_forgejo_url()

    def test_get_package_owner_from_package_owner(self) -> None:
        with patch(
            "forge.services.install.load_config",
            return_value={"forgejo": {"package_owner": "myorg"}},
        ):
            assert _get_package_owner() == "myorg"

    def test_get_package_owner_from_default_owner(self) -> None:
        with patch(
            "forge.services.install.load_config",
            return_value={"forgejo": {"default_owner": "fallback"}},
        ):
            assert _get_package_owner() == "fallback"

    def test_get_package_owner_empty(self) -> None:
        with patch("forge.services.install.load_config", return_value={}):
            assert _get_package_owner() == ""

    def test_get_forgejo_token_from_env(self) -> None:
        with (
            patch.dict("os.environ", {"FORGE_FORGEJO__TOKEN": "env-token"}),
            patch("forge.services.install.load_config", return_value={}),
        ):
            assert _get_forgejo_token() == "env-token"

    def test_get_forgejo_token_from_config(self) -> None:
        with (
            patch.dict("os.environ", {}, clear=True),
            patch(
                "forge.services.install.load_config",
                return_value={"forgejo": {"token": "cfg-token"}},
            ),
        ):
            assert _get_forgejo_token() == "cfg-token"

    def test_get_forgejo_token_from_op(self) -> None:
        with (
            patch.dict("os.environ", {}, clear=True),
            patch(
                "forge.services.install.load_config",
                return_value={"forgejo": {"token_op_ref": "op://vault/item/field"}},
            ),
            patch("forge.services.install.subprocess.run") as mock_run,
        ):
            mock_run.return_value = MagicMock(returncode=0, stdout="op-token\n")
            assert _get_forgejo_token() == "op-token"
            mock_run.assert_called_once_with(
                ["op", "read", "op://vault/item/field"],
                capture_output=True,
                text=True,
                check=False,
            )

    def test_get_forgejo_token_op_fails(self) -> None:
        with (
            patch.dict("os.environ", {}, clear=True),
            patch(
                "forge.services.install.load_config",
                return_value={"forgejo": {"token_op_ref": "op://vault/item/field"}},
            ),
            patch("forge.services.install.subprocess.run") as mock_run,
        ):
            mock_run.return_value = MagicMock(returncode=1)
            assert _get_forgejo_token() == ""

    def test_get_forgejo_token_empty(self) -> None:
        with (
            patch.dict("os.environ", {}, clear=True),
            patch("forge.services.install.load_config", return_value={"forgejo": {}}),
        ):
            assert _get_forgejo_token() == ""


class TestSerializeToml:
    """Tests for _serialize_toml."""

    def test_string_value(self) -> None:
        result = _serialize_toml({"key": "value"})
        assert 'key = "value"' in result

    def test_bool_values(self) -> None:
        result = _serialize_toml({"a": True, "b": False})
        assert "a = true" in result
        assert "b = false" in result

    def test_int_value(self) -> None:
        result = _serialize_toml({"count": 42})
        assert "count = 42" in result

    def test_float_value(self) -> None:
        result = _serialize_toml({"rate": 3.14})
        assert "rate = 3.14" in result

    def test_single_item_list(self) -> None:
        result = _serialize_toml({"urls": ["https://example.com"]})
        assert 'urls = ["https://example.com"]' in result

    def test_multi_item_list(self) -> None:
        result = _serialize_toml({"urls": ["https://a.com", "https://b.com"]})
        assert 'urls = ["https://a.com", "https://b.com"]' in result


class TestGetOsRelease:
    """Tests for _get_os_release."""

    def test_parses_os_release(self, tmp_path: Path) -> None:
        os_release = tmp_path / "os-release"
        os_release.write_text('ID=debian\nVERSION_CODENAME="trixie"\nID_LIKE=\n')
        with patch("forge.services.install.Path") as mock_path:
            mock_path.return_value = os_release
            result = _get_os_release()
            assert result["ID"] == "debian"
            assert result["VERSION_CODENAME"] == "trixie"

    def test_missing_file(self) -> None:
        with patch("forge.services.install.Path") as mock_path:
            mock_path.return_value.exists.return_value = False
            result = _get_os_release()
            assert result == {}


class TestInstallServicePypi:
    """Tests for InstallService.pypi()."""

    def test_pypi_adds_index(self, tmp_path: Path) -> None:
        uv_config = tmp_path / ".config" / "uv" / "uv.toml"
        with (
            patch(
                "forge.services.install.load_config",
                return_value={"forgejo": {"package_owner": "myorg"}},
            ),
            patch("forge.services.install.Path.home", return_value=tmp_path),
        ):
            svc = InstallService(_auto_register=False)
            result = svc.pypi()
            assert "Added PyPI index" in result
            assert uv_config.exists()
            content = uv_config.read_text()
            assert "myorg" in content

    def test_pypi_already_configured(self, tmp_path: Path) -> None:
        uv_config = tmp_path / ".config" / "uv" / "uv.toml"
        uv_config.parent.mkdir(parents=True, exist_ok=True)
        url = "https://git.app.home.southroute.com/api/packages/myorg/pypi/simple/"
        uv_config.write_text(f'extra-index-url = ["{url}"]\n')
        with (
            patch(
                "forge.services.install.load_config",
                return_value={"forgejo": {"package_owner": "myorg"}},
            ),
            patch("forge.services.install.Path.home", return_value=tmp_path),
        ):
            svc = InstallService(_auto_register=False)
            result = svc.pypi()
            assert "Already configured" in result

    def test_pypi_no_owner(self) -> None:
        with patch("forge.services.install.load_config", return_value={}):
            svc = InstallService(_auto_register=False)
            result = svc.pypi()
            assert "Error" in result
            assert "no owner" in result

    def test_pypi_explicit_owner(self, tmp_path: Path) -> None:
        with (
            patch("forge.services.install.load_config", return_value={}),
            patch("forge.services.install.Path.home", return_value=tmp_path),
        ):
            svc = InstallService(_auto_register=False)
            result = svc.pypi(owner="explicit")
            assert "Added PyPI index" in result
            assert "explicit" in result


class TestInstallServiceDebian:
    """Tests for InstallService.debian()."""

    def test_debian_not_debian_system(self) -> None:
        with (
            patch(
                "forge.services.install._get_os_release",
                return_value={"ID": "alpine", "ID_LIKE": ""},
            ),
            patch("forge.services.install.load_config", return_value={}),
        ):
            svc = InstallService(_auto_register=False)
            result = svc.debian()
            assert "Error" in result
            assert "not a Debian-based system" in result

    def test_debian_no_owner(self) -> None:
        with (
            patch(
                "forge.services.install._get_os_release",
                return_value={"ID": "debian", "ID_LIKE": ""},
            ),
            patch("forge.services.install.load_config", return_value={}),
        ):
            svc = InstallService(_auto_register=False)
            result = svc.debian()
            assert "Error" in result
            assert "no owner" in result

    def test_debian_no_codename(self) -> None:
        with (
            patch(
                "forge.services.install._get_os_release",
                return_value={"ID": "debian", "ID_LIKE": ""},
            ),
            patch(
                "forge.services.install.load_config",
                return_value={"forgejo": {"package_owner": "org"}},
            ),
        ):
            svc = InstallService(_auto_register=False)
            result = svc.debian()
            assert "Error" in result
            assert "codename" in result

    def test_debian_no_token(self) -> None:
        with (
            patch(
                "forge.services.install._get_os_release",
                return_value={
                    "ID": "debian",
                    "ID_LIKE": "",
                    "VERSION_CODENAME": "trixie",
                },
            ),
            patch(
                "forge.services.install.load_config",
                return_value={"forgejo": {"package_owner": "org"}},
            ),
            patch.dict("os.environ", {}, clear=True),
        ):
            svc = InstallService(_auto_register=False)
            result = svc.debian()
            assert "Error" in result
            assert "token" in result.lower()

    def test_debian_already_configured(self) -> None:
        with (
            patch(
                "forge.services.install._get_os_release",
                return_value={
                    "ID": "debian",
                    "ID_LIKE": "",
                    "VERSION_CODENAME": "trixie",
                },
            ),
            patch(
                "forge.services.install.load_config",
                return_value={"forgejo": {"package_owner": "org", "token": "tok"}},
            ),
            patch.dict("os.environ", {}, clear=True),
            patch("forge.services.install.subprocess.run") as mock_run,
            patch("forge.services.install.Path") as mock_path_cls,
        ):
            # dpkg --print-architecture
            mock_run.return_value = MagicMock(returncode=0, stdout="amd64\n")

            mock_sources = MagicMock()
            mock_sources.exists.return_value = True
            mock_sources.read_text.return_value = (
                "deb [arch=amd64 trusted=yes] "
                "https://git.app.home.southroute.com/api/packages/org/debian trixie main"
            )

            def path_side_effect(arg: str = "") -> MagicMock:
                if arg == "/etc/apt/sources.list.d/forgejo.list":
                    return mock_sources
                return MagicMock(exists=MagicMock(return_value=False))

            mock_path_cls.side_effect = path_side_effect

            svc = InstallService(_auto_register=False)
            result = svc.debian()
            assert "Already configured" in result

    def test_debian_success(self) -> None:
        with (
            patch(
                "forge.services.install._get_os_release",
                return_value={
                    "ID": "debian",
                    "ID_LIKE": "",
                    "VERSION_CODENAME": "trixie",
                },
            ),
            patch(
                "forge.services.install.load_config",
                return_value={"forgejo": {"package_owner": "org", "token": "tok"}},
            ),
            patch.dict("os.environ", {}, clear=True),
            patch("forge.services.install.subprocess.run") as mock_run,
            patch("forge.services.install.Path") as mock_path_cls,
        ):
            mock_run.return_value = MagicMock(returncode=0, stdout="amd64\n")

            mock_sources = MagicMock()
            mock_sources.exists.return_value = False
            mock_auth = MagicMock()

            def path_side_effect(arg: str = "") -> MagicMock:
                if arg == "/etc/apt/sources.list.d/forgejo.list":
                    return mock_sources
                if arg == "/etc/apt/auth.conf.d/forgejo.conf":
                    return mock_auth
                return MagicMock(exists=MagicMock(return_value=False))

            mock_path_cls.side_effect = path_side_effect

            svc = InstallService(_auto_register=False)
            result = svc.debian()
            assert "Added Debian repository" in result

    def test_debian_auth_write_error(self) -> None:
        with (
            patch(
                "forge.services.install._get_os_release",
                return_value={
                    "ID": "debian",
                    "ID_LIKE": "",
                    "VERSION_CODENAME": "trixie",
                },
            ),
            patch(
                "forge.services.install.load_config",
                return_value={"forgejo": {"package_owner": "org", "token": "tok"}},
            ),
            patch.dict("os.environ", {}, clear=True),
            patch("forge.services.install.subprocess.run") as mock_run,
            patch("forge.services.install.Path") as mock_path_cls,
        ):
            # First call: dpkg --print-architecture succeeds
            # Second call: sudo tee auth fails
            mock_run.side_effect = [
                MagicMock(returncode=0, stdout="amd64\n"),
                subprocess.CalledProcessError(1, "sudo", stderr="permission denied"),
            ]

            mock_sources = MagicMock()
            mock_sources.exists.return_value = False
            mock_auth = MagicMock()

            def path_side_effect(arg: str = "") -> MagicMock:
                if arg == "/etc/apt/sources.list.d/forgejo.list":
                    return mock_sources
                if arg == "/etc/apt/auth.conf.d/forgejo.conf":
                    return mock_auth
                return MagicMock(exists=MagicMock(return_value=False))

            mock_path_cls.side_effect = path_side_effect

            svc = InstallService(_auto_register=False)
            result = svc.debian()
            assert "Error writing" in result

    def test_debian_apt_update_error(self) -> None:
        with (
            patch(
                "forge.services.install._get_os_release",
                return_value={
                    "ID": "debian",
                    "ID_LIKE": "",
                    "VERSION_CODENAME": "trixie",
                },
            ),
            patch(
                "forge.services.install.load_config",
                return_value={"forgejo": {"package_owner": "org", "token": "tok"}},
            ),
            patch.dict("os.environ", {}, clear=True),
            patch("forge.services.install.subprocess.run") as mock_run,
            patch("forge.services.install.Path") as mock_path_cls,
        ):
            # dpkg, auth, chmod, sources succeed; apt-get update fails
            mock_run.side_effect = [
                MagicMock(returncode=0, stdout="amd64\n"),  # dpkg --print-architecture
                MagicMock(returncode=0),  # sudo tee auth_file
                MagicMock(returncode=0),  # sudo chmod 600
                MagicMock(returncode=0),  # sudo tee sources_file
                subprocess.CalledProcessError(1, "apt-get", stderr="update failed"),
            ]

            mock_sources = MagicMock()
            mock_sources.exists.return_value = False
            mock_auth = MagicMock()

            def path_side_effect(arg: str = "") -> MagicMock:
                if arg == "/etc/apt/sources.list.d/forgejo.list":
                    return mock_sources
                if arg == "/etc/apt/auth.conf.d/forgejo.conf":
                    return mock_auth
                return MagicMock(exists=MagicMock(return_value=False))

            mock_path_cls.side_effect = path_side_effect

            svc = InstallService(_auto_register=False)
            result = svc.debian()
            assert "apt-get update failed" in result

    def test_debian_sources_write_error(self) -> None:
        with (
            patch(
                "forge.services.install._get_os_release",
                return_value={
                    "ID": "debian",
                    "ID_LIKE": "",
                    "VERSION_CODENAME": "trixie",
                },
            ),
            patch(
                "forge.services.install.load_config",
                return_value={"forgejo": {"package_owner": "org", "token": "tok"}},
            ),
            patch.dict("os.environ", {}, clear=True),
            patch("forge.services.install.subprocess.run") as mock_run,
            patch("forge.services.install.Path") as mock_path_cls,
        ):
            mock_run.side_effect = [
                MagicMock(returncode=0, stdout="amd64\n"),  # dpkg
                MagicMock(returncode=0),  # sudo tee auth
                MagicMock(returncode=0),  # sudo chmod
                subprocess.CalledProcessError(1, "sudo", stderr="write failed"),  # sudo tee sources
            ]

            mock_sources = MagicMock()
            mock_sources.exists.return_value = False
            mock_auth = MagicMock()

            def path_side_effect(arg: str = "") -> MagicMock:
                if arg == "/etc/apt/sources.list.d/forgejo.list":
                    return mock_sources
                if arg == "/etc/apt/auth.conf.d/forgejo.conf":
                    return mock_auth
                return MagicMock(exists=MagicMock(return_value=False))

            mock_path_cls.side_effect = path_side_effect

            svc = InstallService(_auto_register=False)
            result = svc.debian()
            assert "Error writing" in result

    def test_debian_ubuntu_like(self) -> None:
        """Ubuntu-like systems (ID_LIKE contains 'debian') should work."""
        with (
            patch(
                "forge.services.install._get_os_release",
                return_value={
                    "ID": "ubuntu",
                    "ID_LIKE": "debian",
                    "VERSION_CODENAME": "noble",
                },
            ),
            patch(
                "forge.services.install.load_config",
                return_value={"forgejo": {"package_owner": "org", "token": "tok"}},
            ),
            patch.dict("os.environ", {}, clear=True),
            patch("forge.services.install.subprocess.run") as mock_run,
            patch("forge.services.install.Path") as mock_path_cls,
        ):
            mock_run.return_value = MagicMock(returncode=0, stdout="amd64\n")

            mock_sources = MagicMock()
            mock_sources.exists.return_value = False

            def path_side_effect(arg: str = "") -> MagicMock:
                if arg == "/etc/apt/sources.list.d/forgejo.list":
                    return mock_sources
                return MagicMock(exists=MagicMock(return_value=False))

            mock_path_cls.side_effect = path_side_effect

            svc = InstallService(_auto_register=False)
            result = svc.debian()
            assert "Added Debian repository" in result

    def test_debian_dpkg_fails_defaults_to_amd64(self) -> None:
        """When dpkg --print-architecture fails, default to amd64."""
        with (
            patch(
                "forge.services.install._get_os_release",
                return_value={
                    "ID": "debian",
                    "ID_LIKE": "",
                    "VERSION_CODENAME": "trixie",
                },
            ),
            patch(
                "forge.services.install.load_config",
                return_value={"forgejo": {"package_owner": "org", "token": "tok"}},
            ),
            patch.dict("os.environ", {}, clear=True),
            patch("forge.services.install.subprocess.run") as mock_run,
            patch("forge.services.install.Path") as mock_path_cls,
        ):
            mock_run.side_effect = [
                subprocess.CalledProcessError(1, "dpkg"),  # dpkg fails
                MagicMock(returncode=0),  # sudo tee auth
                MagicMock(returncode=0),  # chmod
                MagicMock(returncode=0),  # sudo tee sources
                MagicMock(returncode=0),  # apt-get update
            ]

            mock_sources = MagicMock()
            mock_sources.exists.return_value = False

            def path_side_effect(arg: str = "") -> MagicMock:
                if arg == "/etc/apt/sources.list.d/forgejo.list":
                    return mock_sources
                return MagicMock(exists=MagicMock(return_value=False))

            mock_path_cls.side_effect = path_side_effect

            svc = InstallService(_auto_register=False)
            result = svc.debian()
            assert "Added Debian repository" in result
            assert "amd64" in result
