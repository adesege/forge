"""Tests for the package service."""

from __future__ import annotations

import io
import json
import struct
import tarfile

import pytest

from forge.services import package
from forge.services.package import _build_cargo_payload, _extract_cargo_toml


class TestPackageService:
    """Tests for package service functions."""

    def test_list(self, mock_forgejo_client) -> None:  # type: ignore[no-untyped-def]
        mock_forgejo_client.get.return_value = [
            {
                "name": "my-pkg",
                "type": "generic",
                "version": "1.0.0",
                "creator": {"login": "dev"},
                "created_at": "2026-01-01",
            },
        ]
        result = package.list_packages(owner="testuser")
        assert "my-pkg" in result

    def test_list_empty(self, mock_forgejo_client) -> None:  # type: ignore[no-untyped-def]
        mock_forgejo_client.get.return_value = []
        result = package.list_packages(owner="testuser")
        assert "No packages found" in result

    def test_list_with_type_filter(self, mock_forgejo_client) -> None:  # type: ignore[no-untyped-def]
        mock_forgejo_client.get.return_value = [
            {
                "name": "my-pkg",
                "type": "pypi",
                "version": "2.0.0",
                "creator": {"login": "dev"},
                "created_at": "2026-01-01",
            },
        ]
        result = package.list_packages(owner="testuser", type="pypi")
        mock_forgejo_client.get.assert_called_once_with(
            "/packages/testuser",
            params={"limit": 30, "page": 1, "type": "pypi"},
        )
        assert "my-pkg" in result

    def test_view(self, mock_forgejo_client) -> None:  # type: ignore[no-untyped-def]
        mock_forgejo_client.get.return_value = {
            "name": "my-pkg",
            "type": "generic",
            "version": "1.0.0",
            "creator": {"login": "dev"},
            "created_at": "2026-01-01",
            "html_url": "https://example.com/packages/my-pkg",
        }
        result = package.view_package(name="my-pkg", version="1.0.0", type="generic", owner="o")
        assert "my-pkg" in result

    def test_view_missing_name(self) -> None:
        result = package.view_package(version="1.0.0", type="generic", owner="o")
        assert "Error" in result

    def test_view_missing_version(self) -> None:
        result = package.view_package(name="pkg", type="generic", owner="o")
        assert "Error" in result

    def test_view_missing_type(self) -> None:
        result = package.view_package(name="pkg", version="1.0.0", owner="o")
        assert "Error" in result

    def test_files(self, mock_forgejo_client) -> None:  # type: ignore[no-untyped-def]
        mock_forgejo_client.get.return_value = [
            {"name": "file.bin", "size": 1024, "md5": "abc123"},
        ]
        result = package.files(name="my-pkg", version="1.0.0", type="generic", owner="o")
        assert "file.bin" in result

    def test_files_empty(self, mock_forgejo_client) -> None:  # type: ignore[no-untyped-def]
        mock_forgejo_client.get.return_value = []
        result = package.files(name="my-pkg", version="1.0.0", type="generic", owner="o")
        assert "No files found" in result

    def test_delete(self, mock_forgejo_client) -> None:  # type: ignore[no-untyped-def]
        mock_forgejo_client.delete.return_value = None
        result = package.delete_package(name="my-pkg", version="1.0.0", type="generic", owner="o")
        assert "Deleted" in result

    def test_delete_missing_name(self) -> None:
        result = package.delete_package(version="1.0.0", type="generic", owner="o")
        assert "Error" in result

    def test_publish(self, mock_forgejo_client, tmp_path) -> None:  # type: ignore[no-untyped-def]
        test_file = tmp_path / "artifact.bin"
        test_file.write_bytes(b"hello")
        mock_forgejo_client.put_file.return_value = None
        result = package.publish(name="my-pkg", version="1.0.0", file=str(test_file), owner="o")
        assert "Published" in result
        assert "artifact.bin" in result
        mock_forgejo_client.put_file.assert_called_once_with(
            "/api/packages/o/generic/my-pkg/1.0.0/artifact.bin",
            content=b"hello",
        )

    def test_publish_missing_file(self) -> None:
        result = package.publish(name="pkg", version="1.0.0", owner="o")
        assert "Error" in result

    def test_publish_file_not_found(self) -> None:
        result = package.publish(
            name="pkg", version="1.0.0", file="/nonexistent/file.bin", owner="o"
        )
        assert "Error" in result
        assert "not found" in result

    def test_download(self, mock_forgejo_client, tmp_path) -> None:  # type: ignore[no-untyped-def]
        mock_forgejo_client.download_file.return_value = b"file content"
        out_path = str(tmp_path / "output.bin")
        result = package.download(
            name="my-pkg",
            version="1.0.0",
            filename="artifact.bin",
            output=out_path,
            owner="o",
        )
        assert "Downloaded" in result
        with open(out_path, "rb") as f:
            assert f.read() == b"file content"

    def test_download_missing_filename(self) -> None:
        result = package.download(name="pkg", version="1.0.0", owner="o")
        assert "Error" in result

    def test_publish_deb(self, mock_forgejo_client, tmp_path) -> None:  # type: ignore[no-untyped-def]
        deb_file = tmp_path / "forge_1.0.0_all.deb"
        deb_file.write_bytes(b"deb-content")
        mock_forgejo_client.put_file.return_value = None
        result = package.publish_deb(file=str(deb_file), owner="o")
        assert "Published" in result
        assert "trixie/main" in result
        mock_forgejo_client.put_file.assert_called_once_with(
            "/api/packages/o/debian/pool/trixie/main/upload",
            content=b"deb-content",
        )

    def test_publish_deb_custom_pool(self, mock_forgejo_client, tmp_path) -> None:  # type: ignore[no-untyped-def]
        deb_file = tmp_path / "forge_1.0.0_all.deb"
        deb_file.write_bytes(b"deb-content")
        mock_forgejo_client.put_file.return_value = None
        result = package.publish_deb(
            file=str(deb_file), owner="o", distribution="bookworm", component="contrib"
        )
        assert "Published" in result
        assert "bookworm/contrib" in result
        mock_forgejo_client.put_file.assert_called_once_with(
            "/api/packages/o/debian/pool/bookworm/contrib/upload",
            content=b"deb-content",
        )

    def test_publish_deb_missing_file(self) -> None:
        result = package.publish_deb(owner="o")
        assert "Error" in result

    def test_publish_deb_file_not_found(self) -> None:
        result = package.publish_deb(file="/nonexistent/file.deb", owner="o")
        assert "Error" in result
        assert "not found" in result


def _make_crate(tmp_path, name="my-crate", version="0.1.0", extra_toml=""):  # type: ignore[no-untyped-def]
    """Create a minimal .crate file (gzipped tar with Cargo.toml)."""
    cargo_toml_content = f"""\
[package]
name = "{name}"
version = "{version}"
edition = "2021"
description = "A test crate"
license = "MIT"
{extra_toml}
"""
    crate_path = tmp_path / f"{name}-{version}.crate"
    with tarfile.open(str(crate_path), "w:gz") as tar:
        data = cargo_toml_content.encode("utf-8")
        info = tarfile.TarInfo(name=f"{name}-{version}/Cargo.toml")
        info.size = len(data)
        tar.addfile(info, io.BytesIO(data))
    return str(crate_path)


class TestPublishCrate:
    """Tests for publish_crate and its helpers."""

    def test_extract_cargo_toml(self, tmp_path) -> None:  # type: ignore[no-untyped-def]
        crate_path = _make_crate(tmp_path)
        toml_data = _extract_cargo_toml(crate_path)
        assert toml_data["package"]["name"] == "my-crate"
        assert toml_data["package"]["version"] == "0.1.0"

    def test_extract_cargo_toml_missing(self, tmp_path) -> None:  # type: ignore[no-untyped-def]
        # Create a tarball without Cargo.toml
        crate_path = str(tmp_path / "bad.crate")
        with tarfile.open(crate_path, "w:gz") as tar:
            data = b"hello"
            info = tarfile.TarInfo(name="some-file.txt")
            info.size = len(data)
            tar.addfile(info, io.BytesIO(data))
        with pytest.raises(ValueError, match="Cargo.toml not found"):
            _extract_cargo_toml(crate_path)

    def test_build_cargo_payload_structure(self, tmp_path) -> None:  # type: ignore[no-untyped-def]
        extra = """\
[dependencies]
serde = "1.0"

[dev-dependencies]
pretty_assertions = "1.0"
"""
        crate_path = _make_crate(tmp_path, extra_toml=extra)
        payload = _build_cargo_payload(crate_path)

        # Decode the wire format
        json_len = struct.unpack("<I", payload[:4])[0]
        json_data = json.loads(payload[4 : 4 + json_len])
        crate_len = struct.unpack("<I", payload[4 + json_len : 8 + json_len])[0]
        crate_data = payload[8 + json_len :]

        assert json_data["name"] == "my-crate"
        assert json_data["vers"] == "0.1.0"
        assert json_data["license"] == "MIT"
        assert json_data["description"] == "A test crate"
        assert len(json_data["deps"]) == 2
        assert crate_len == len(crate_data)

        # Verify deps
        dep_names = {d["name"] for d in json_data["deps"]}
        assert "serde" in dep_names
        assert "pretty_assertions" in dep_names
        serde_dep = next(d for d in json_data["deps"] if d["name"] == "serde")
        assert serde_dep["kind"] == "normal"
        assert serde_dep["version_req"] == "1.0"
        pa_dep = next(d for d in json_data["deps"] if d["name"] == "pretty_assertions")
        assert pa_dep["kind"] == "dev"

    def test_publish_crate_success(self, mock_forgejo_client, tmp_path) -> None:  # type: ignore[no-untyped-def]
        crate_path = _make_crate(tmp_path)
        mock_forgejo_client.put_file.return_value = None
        result = package.publish_crate(file=crate_path, owner="o")
        assert "Published" in result
        assert "my-crate" in result
        assert "0.1.0" in result
        mock_forgejo_client.put_file.assert_called_once()
        call_args = mock_forgejo_client.put_file.call_args
        assert call_args[0][0] == "/api/packages/o/cargo/api/v1/crates/new"

    def test_publish_crate_missing_file(self) -> None:
        result = package.publish_crate(owner="o")
        assert "Error" in result

    def test_publish_crate_file_not_found(self) -> None:
        result = package.publish_crate(file="/nonexistent/crate.crate", owner="o")
        assert "Error" in result
        assert "not found" in result

    def test_publish_crate_wrong_extension(self, tmp_path) -> None:  # type: ignore[no-untyped-def]
        bad_file = tmp_path / "something.tar.gz"
        bad_file.write_bytes(b"data")
        result = package.publish_crate(file=str(bad_file), owner="o")
        assert "Error" in result
        assert ".crate" in result

    def test_publish_crate_with_complex_deps(self, mock_forgejo_client, tmp_path) -> None:  # type: ignore[no-untyped-def]
        extra = """\
[dependencies]
serde = { version = "1.0", features = ["derive"] }
renamed = { version = "2.0", package = "actual-name" }

[target.'cfg(unix)'.dependencies]
openssl = "0.10"
"""
        crate_path = _make_crate(tmp_path, extra_toml=extra)
        mock_forgejo_client.put_file.return_value = None
        result = package.publish_crate(file=crate_path, owner="o")
        assert "Published" in result

        # Verify the payload structure
        call_args = mock_forgejo_client.put_file.call_args
        payload = call_args[1]["content"] if "content" in (call_args[1] or {}) else call_args[0][1]
        json_len = struct.unpack("<I", payload[:4])[0]
        json_data = json.loads(payload[4 : 4 + json_len])

        dep_names = {d["name"] for d in json_data["deps"]}
        assert "serde" in dep_names
        assert "actual-name" in dep_names
        assert "openssl" in dep_names

        serde_dep = next(d for d in json_data["deps"] if d["name"] == "serde")
        assert serde_dep["features"] == ["derive"]

        renamed_dep = next(d for d in json_data["deps"] if d["name"] == "actual-name")
        assert renamed_dep["explicit_name_in_toml"] == "renamed"

        openssl_dep = next(d for d in json_data["deps"] if d["name"] == "openssl")
        assert openssl_dep["target"] == "cfg(unix)"
