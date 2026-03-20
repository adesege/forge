"""Package service — manage Forgejo packages."""

from __future__ import annotations

import io
import json
import os
import struct
import tarfile
import tomllib
from typing import Any

from click_clop.service import Service

from forge.forgejo import get_client
from forge.forgejo.context import get_default_owner
from forge.forgejo.formatting import format_package, format_table


def _extract_cargo_toml(crate_path: str) -> dict[str, Any]:
    """Extract and parse Cargo.toml from a .crate file (gzipped tar)."""
    with tarfile.open(crate_path, "r:gz") as tar:
        for member in tar.getmembers():
            # Cargo.toml is at {name}-{version}/Cargo.toml
            if member.name.endswith("/Cargo.toml") and member.name.count("/") == 1:
                f = tar.extractfile(member)
                if f is None:
                    raise ValueError(f"Could not read {member.name} from crate")
                return tomllib.load(f)
    raise ValueError("Cargo.toml not found in .crate file")


def _parse_deps(cargo_toml: dict[str, Any], kind: str, section: str) -> list[dict[str, Any]]:
    """Parse dependencies from a Cargo.toml section into registry format."""
    deps_section = cargo_toml.get(section, {})
    result: list[dict[str, Any]] = []
    for name, spec in deps_section.items():
        if isinstance(spec, str):
            dep: dict[str, Any] = {
                "name": name,
                "version_req": spec,
                "features": [],
                "optional": False,
                "default_features": True,
                "target": None,
                "kind": kind,
                "registry": None,
                "explicit_name_in_toml": None,
            }
        else:
            dep = {
                "name": spec.get("package", name),
                "version_req": spec.get("version", "*"),
                "features": spec.get("features", []),
                "optional": spec.get("optional", False),
                "default_features": spec.get("default-features", True),
                "target": None,
                "kind": kind,
                "registry": spec.get("registry", None),
                "explicit_name_in_toml": name if spec.get("package") else None,
            }
        result.append(dep)
    return result


def _build_target_deps(cargo_toml: dict[str, Any]) -> list[dict[str, Any]]:
    """Parse target-specific dependencies."""
    result: list[dict[str, Any]] = []
    for target, sections in cargo_toml.get("target", {}).items():
        for section, kind in [
            ("dependencies", "normal"),
            ("dev-dependencies", "dev"),
            ("build-dependencies", "build"),
        ]:
            for name, spec in sections.get(section, {}).items():
                if isinstance(spec, str):
                    dep: dict[str, Any] = {
                        "name": name,
                        "version_req": spec,
                        "features": [],
                        "optional": False,
                        "default_features": True,
                        "target": target,
                        "kind": kind,
                        "registry": None,
                        "explicit_name_in_toml": None,
                    }
                else:
                    dep = {
                        "name": spec.get("package", name),
                        "version_req": spec.get("version", "*"),
                        "features": spec.get("features", []),
                        "optional": spec.get("optional", False),
                        "default_features": spec.get("default-features", True),
                        "target": target,
                        "kind": kind,
                        "registry": spec.get("registry", None),
                        "explicit_name_in_toml": name if spec.get("package") else None,
                    }
                result.append(dep)
    return result


def _build_cargo_payload(crate_path: str) -> bytes:
    """Build the Cargo registry wire-format payload from a .crate file.

    Wire format:
        [u32 LE: JSON metadata length][JSON bytes][u32 LE: crate length][crate bytes]
    """
    cargo_toml = _extract_cargo_toml(crate_path)
    pkg = cargo_toml.get("package", {})

    # Collect all dependencies
    deps: list[dict[str, Any]] = []
    deps.extend(_parse_deps(cargo_toml, "normal", "dependencies"))
    deps.extend(_parse_deps(cargo_toml, "dev", "dev-dependencies"))
    deps.extend(_parse_deps(cargo_toml, "build", "build-dependencies"))
    deps.extend(_build_target_deps(cargo_toml))

    metadata = {
        "name": pkg.get("name", ""),
        "vers": pkg.get("version", ""),
        "deps": deps,
        "features": cargo_toml.get("features", {}),
        "authors": pkg.get("authors", []),
        "description": pkg.get("description"),
        "documentation": pkg.get("documentation"),
        "homepage": pkg.get("homepage"),
        "readme": pkg.get("readme"),
        "readme_file": pkg.get("readme"),
        "keywords": pkg.get("keywords", []),
        "categories": pkg.get("categories", []),
        "license": pkg.get("license"),
        "license_file": pkg.get("license-file"),
        "repository": pkg.get("repository"),
        "links": pkg.get("links"),
    }

    json_bytes = json.dumps(metadata).encode("utf-8")
    with open(crate_path, "rb") as f:
        crate_bytes = f.read()

    buf = io.BytesIO()
    buf.write(struct.pack("<I", len(json_bytes)))
    buf.write(json_bytes)
    buf.write(struct.pack("<I", len(crate_bytes)))
    buf.write(crate_bytes)
    return buf.getvalue()


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

    def publish_deb(
        self,
        file: str = "",
        owner: str = "",
        distribution: str = "trixie",
        component: str = "main",
    ) -> str:
        """Publish a .deb package to the Forgejo Debian registry.

        Args:
            file: Path to the .deb file to upload.
            owner: Package owner. Inferred from config if omitted.
            distribution: Debian distribution (e.g. trixie, bookworm, noble).
            component: Repository component (e.g. main, contrib, non-free).
        """
        if not owner:
            owner = get_default_owner()
        if not file:
            return "Error: --file is required."
        if not os.path.isfile(file):
            return f"Error: file not found: {file}"
        filename = os.path.basename(file)
        with open(file, "rb") as f:
            content = f.read()
        client = get_client()
        client.put_file(
            f"/api/packages/{owner}/debian/pool/{distribution}/{component}/upload",
            content=content,
        )
        return f"Published {filename} to debian pool {distribution}/{component}"

    def publish_crate(
        self,
        file: str = "",
        owner: str = "",
    ) -> str:
        """Publish a Rust crate to the Forgejo Cargo registry.

        The file should be a .crate file produced by 'cargo package'.

        Args:
            file: Path to the .crate file to upload.
            owner: Package owner. Inferred from config if omitted.
        """
        if not owner:
            owner = get_default_owner()
        if not file:
            return "Error: --file is required."
        if not os.path.isfile(file):
            return f"Error: file not found: {file}"
        if not file.endswith(".crate"):
            return "Error: file must be a .crate file (produced by 'cargo package')."
        try:
            payload = _build_cargo_payload(file)
        except (ValueError, KeyError, tarfile.TarError) as exc:
            return f"Error: failed to parse crate: {exc}"
        # Extract name/version for the success message
        cargo_toml = _extract_cargo_toml(file)
        pkg = cargo_toml.get("package", {})
        name = pkg.get("name", os.path.basename(file))
        version = pkg.get("version", "unknown")
        client = get_client()
        client.put_file(
            f"/api/packages/{owner}/cargo/api/v1/crates/new",
            content=payload,
        )
        return f"Published crate {name} {version} to cargo registry"

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
