"""MCP server for forge.

Exposes all service methods as MCP tools.
"""

from __future__ import annotations

from click_clop import expose_mcp
from fastmcp import FastMCP

import forge.services  # noqa: F401 — triggers auto-registration


def create_mcp() -> FastMCP:
    """Create the FastMCP server with all service tools."""
    mcp = FastMCP("forge")
    expose_mcp(mcp)
    return mcp
