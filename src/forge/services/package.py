"""Package service — manage Forgejo packages."""

from __future__ import annotations

import os
from typing import Any

from click_clop.service import Service

from forge.forgejo import get_client
from forge.forgejo.context import get_default_owner
from forge.forgejo.formatting import format_package, format_table


class PackageService(Service):
    """Forgejo package registry operations."""

    name = "package"
    description = "Manage packages"

    def list(
        self,
        owner: str = "",
        type: str = "",
        query: str = "",
        limit: int = 30,
        page: int = 1,
    ) -> str:
        """List packages for an owner.

        Args:
            owner: Package owner (user or org). Inferred from config if omitted.
            type: Filter by package type (e.g. generic, pypi, npm, debian).
            query: Search query string.
            limit: Maximum number of results.
            page: Page number.
        """
        if not owner:
            owner = get_default_owner()
        client = get_client()
        params: dict[str, Any] = {"limit": limit, "page": page}
        if type:
            params["type"] = type
        if query:
            params["q"] = query
        data = client.get(f"/packages/{owner}", params=params)
        if not data:
            return "No packages found."
        return format_table(
            data,
            [
                ("name", "Name"),
                ("type", "Type"),
                ("version", "Version"),
                ("creator", "Creator"),
                ("created_at", "Created"),
            ],
            title=f"Packages — {owner}",
        )

    def view(
        self,
        name: str = "",
        version: str = "",
        type: str = "",
        owner: str = "",
    ) -> str:
        """View package version details.

        Args:
            name: Package name.
            version: Package version.
            type: Package type (e.g. generic, pypi, npm, debian).
            owner: Package owner. Inferred from config if omitted.
        """
        if not owner:
            owner = get_default_owner()
        if not name:
            return "Error: --name is required."
        if not version:
            return "Error: --version is required."
        if not type:
            return "Error: --type is required."
        client = get_client()
        data = client.get(f"/packages/{owner}/{type}/{name}/{version}")
        return format_package(data)

    def files(
        self,
        name: str = "",
        version: str = "",
        type: str = "",
        owner: str = "",
    ) -> str:
        """List files in a package version.

        Args:
            name: Package name.
            version: Package version.
            type: Package type (e.g. generic, pypi, npm, debian).
            owner: Package owner. Inferred from config if omitted.
        """
        if not owner:
            owner = get_default_owner()
        if not name:
            return "Error: --name is required."
        if not version:
            return "Error: --version is required."
        if not type:
            return "Error: --type is required."
        client = get_client()
        data = client.get(f"/packages/{owner}/{type}/{name}/{version}/files")
        if not data:
            return "No files found."
        return format_table(
            data,
            [
                ("name", "Filename"),
                ("size", "Size"),
                ("md5", "MD5"),
            ],
            title=f"Files — {name} {version}",
        )

    def delete(
        self,
        name: str = "",
        version: str = "",
        type: str = "",
        owner: str = "",
    ) -> str:
        """Delete a package version.

        Args:
            name: Package name.
            version: Package version.
            type: Package type (e.g. generic, pypi, npm, debian).
            owner: Package owner. Inferred from config if omitted.
        """
        if not owner:
            owner = get_default_owner()
        if not name:
            return "Error: --name is required."
        if not version:
            return "Error: --version is required."
        if not type:
            return "Error: --type is required."
        client = get_client()
        client.delete(f"/packages/{owner}/{type}/{name}/{version}")
        return f"Deleted package: {name} {version}"

    def publish(
        self,
        name: str = "",
        version: str = "",
        file: str = "",
        owner: str = "",
    ) -> str:
        """Publish a file to the generic package registry.

        Args:
            name: Package name.
            version: Package version.
            file: Path to the file to upload.
            owner: Package owner. Inferred from config if omitted.
        """
        if not owner:
            owner = get_default_owner()
        if not name:
            return "Error: --name is required."
        if not version:
            return "Error: --version is required."
        if not file:
            return "Error: --file is required."
        if not os.path.isfile(file):
            return f"Error: file not found: {file}"
        filename = os.path.basename(file)
        with open(file, "rb") as f:
            content = f.read()
        client = get_client()
        client.put_file(
            f"/api/packages/{owner}/generic/{name}/{version}/{filename}",
            content=content,
        )
        return f"Published {filename} to {name}/{version}"

    def download(
        self,
        name: str = "",
        version: str = "",
        filename: str = "",
        output: str = "",
        owner: str = "",
    ) -> str:
        """Download a file from the generic package registry.

        Args:
            name: Package name.
            version: Package version.
            filename: Name of the file to download.
            output: Output path. Defaults to the filename in current directory.
            owner: Package owner. Inferred from config if omitted.
        """
        if not owner:
            owner = get_default_owner()
        if not name:
            return "Error: --name is required."
        if not version:
            return "Error: --version is required."
        if not filename:
            return "Error: --filename is required."
        client = get_client()
        content = client.download_file(
            f"/api/packages/{owner}/generic/{name}/{version}/{filename}",
        )
        out_path = output or filename
        with open(out_path, "wb") as f:
            f.write(content)
        return f"Downloaded {filename} to {out_path}"


_service = PackageService()
