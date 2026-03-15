"""MCP server for forge.

Exposes all service methods as MCP tools.
"""

from __future__ import annotations

from click_clop import expose_mcp
from fastmcp import FastMCP

# Import services so they auto-register
from forge.services import (
    auth,  # noqa: F401
    issue,  # noqa: F401
    org,  # noqa: F401
    pr,  # noqa: F401
    release,  # noqa: F401
    repo,  # noqa: F401
)


def create_mcp() -> FastMCP:
    """Create the FastMCP server with all service tools."""
    mcp = FastMCP("forge")
    expose_mcp(mcp)
    return mcp



