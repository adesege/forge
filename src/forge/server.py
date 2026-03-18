"""MCP server for forge.

Exposes all service methods as MCP tools.
"""

from __future__ import annotations

from click_clop import expose_mcp
from click_clop.config import load_config
from click_clop.logging import setup_logging
from fastmcp import FastMCP

# Import service modules here so they auto-register, e.g.:
#   from forge.services import my_service  # noqa: F401


def create_mcp() -> FastMCP:
    """Create the FastMCP server with all service tools."""
    mcp = FastMCP("forge")
    expose_mcp(mcp)
    return mcp
