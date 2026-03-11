"""MCP server for forge.

Exposes all service methods as MCP tools.
"""

from __future__ import annotations



from fastmcp import FastMCP


from click_clop import expose_mcp, ServiceRegistry
from click_clop.config import load_config
from click_clop.logging import setup_logging


# Import services so they auto-register
from forge.services import hello  # noqa: F401





def create_mcp() -> FastMCP:
    """Create the FastMCP server with all service tools."""
    mcp = FastMCP("forge")
    expose_mcp(mcp)
    return mcp



