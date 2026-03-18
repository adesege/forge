"""Tests for the package service."""

from __future__ import annotations

from forge.services.package import PackageService


class TestPackageService:
    """Tests for PackageService."""

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
        svc = PackageService(_auto_register=False)
        result = svc.list(owner="testuser")
        assert "my-pkg" in result

    def test_list_empty(self, mock_forgejo_client) -> None:  # type: ignore[no-untyped-def]
        mock_forgejo_client.get.return_value = []
        svc = PackageService(_auto_register=False)
        result = svc.list(owner="testuser")
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
        svc = PackageService(_auto_register=False)
        result = svc.list(owner="testuser", type="pypi")
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
        svc = PackageService(_auto_register=False)
        result = svc.view(name="my-pkg", version="1.0.0", type="generic", owner="o")
        assert "my-pkg" in result

    def test_view_missing_name(self) -> None:
        svc = PackageService(_auto_register=False)
        result = svc.view(version="1.0.0", type="generic", owner="o")
        assert "Error" in result

    def test_view_missing_version(self) -> None:
        svc = PackageService(_auto_register=False)
        result = svc.view(name="pkg", type="generic", owner="o")
        assert "Error" in result

    def test_view_missing_type(self) -> None:
        svc = PackageService(_auto_register=False)
        result = svc.view(name="pkg", version="1.0.0", owner="o")
        assert "Error" in result

    def test_files(self, mock_forgejo_client) -> None:  # type: ignore[no-untyped-def]
        mock_forgejo_client.get.return_value = [
            {"name": "file.bin", "size": 1024, "md5": "abc123"},
        ]
        svc = PackageService(_auto_register=False)
        result = svc.files(name="my-pkg", version="1.0.0", type="generic", owner="o")
        assert "file.bin" in result

    def test_files_empty(self, mock_forgejo_client) -> None:  # type: ignore[no-untyped-def]
        mock_forgejo_client.get.return_value = []
        svc = PackageService(_auto_register=False)
        result = svc.files(name="my-pkg", version="1.0.0", type="generic", owner="o")
        assert "No files found" in result

    def test_delete(self, mock_forgejo_client) -> None:  # type: ignore[no-untyped-def]
        mock_forgejo_client.delete.return_value = None
        svc = PackageService(_auto_register=False)
        result = svc.delete(
            name="my-pkg", version="1.0.0", type="generic", owner="o"
        )
        assert "Deleted" in result

    def test_delete_missing_name(self) -> None:
        svc = PackageService(_auto_register=False)
        result = svc.delete(version="1.0.0", type="generic", owner="o")
        assert "Error" in result

    def test_publish(self, mock_forgejo_client, tmp_path) -> None:  # type: ignore[no-untyped-def]
        test_file = tmp_path / "artifact.bin"
        test_file.write_bytes(b"hello")
        mock_forgejo_client.put_file.return_value = None
        svc = PackageService(_auto_register=False)
        result = svc.publish(
            name="my-pkg", version="1.0.0", file=str(test_file), owner="o"
        )
        assert "Published" in result
        assert "artifact.bin" in result
        mock_forgejo_client.put_file.assert_called_once_with(
            "/api/packages/o/generic/my-pkg/1.0.0/artifact.bin",
            content=b"hello",
        )

    def test_publish_missing_file(self) -> None:
        svc = PackageService(_auto_register=False)
        result = svc.publish(name="pkg", version="1.0.0", owner="o")
        assert "Error" in result

    def test_publish_file_not_found(self) -> None:
        svc = PackageService(_auto_register=False)
        result = svc.publish(
            name="pkg", version="1.0.0", file="/nonexistent/file.bin", owner="o"
        )
        assert "Error" in result
        assert "not found" in result

    def test_download(self, mock_forgejo_client, tmp_path) -> None:  # type: ignore[no-untyped-def]
        mock_forgejo_client.download_file.return_value = b"file content"
        svc = PackageService(_auto_register=False)
        out_path = str(tmp_path / "output.bin")
        result = svc.download(
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
        svc = PackageService(_auto_register=False)
        result = svc.download(name="pkg", version="1.0.0", owner="o")
        assert "Error" in result

    def test_publish_deb(self, mock_forgejo_client, tmp_path) -> None:  # type: ignore[no-untyped-def]
        deb_file = tmp_path / "forge_1.0.0_all.deb"
        deb_file.write_bytes(b"deb-content")
        mock_forgejo_client.put_file.return_value = None
        svc = PackageService(_auto_register=False)
        result = svc.publish_deb(file=str(deb_file), owner="o")
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
        svc = PackageService(_auto_register=False)
        result = svc.publish_deb(
            file=str(deb_file), owner="o", distribution="bookworm", component="contrib"
        )
        assert "Published" in result
        assert "bookworm/contrib" in result
        mock_forgejo_client.put_file.assert_called_once_with(
            "/api/packages/o/debian/pool/bookworm/contrib/upload",
            content=b"deb-content",
        )

    def test_publish_deb_missing_file(self) -> None:
        svc = PackageService(_auto_register=False)
        result = svc.publish_deb(owner="o")
        assert "Error" in result

    def test_publish_deb_file_not_found(self) -> None:
        svc = PackageService(_auto_register=False)
        result = svc.publish_deb(file="/nonexistent/file.deb", owner="o")
        assert "Error" in result
        assert "not found" in result
