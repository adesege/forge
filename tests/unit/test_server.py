"""Tests for the MCP server."""

from __future__ import annotations

from fastmcp import FastMCP

from forge.server import create_mcp


class TestCreateMcp:
    """Tests for the create_mcp factory."""

    def test_returns_fastmcp_instance(self) -> None:
        mcp = create_mcp()
        assert isinstance(mcp, FastMCP)

    def test_mcp_has_name(self) -> None:
        mcp = create_mcp()
        assert mcp.name == "forge"
