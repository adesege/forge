"""MCP server for forge.

Exposes service functions as MCP tools.
"""

from __future__ import annotations

from click_clop import expose_mcp
from fastmcp import FastMCP

from forge.services import auth as _auth  # noqa: F401
from forge.services import completion as _completion  # noqa: F401
from forge.services import install as _install  # noqa: F401
from forge.services import issue as _issue  # noqa: F401
from forge.services import org as _org  # noqa: F401
from forge.services import package as _package  # noqa: F401
from forge.services import pr as _pr  # noqa: F401
from forge.services import release as _release  # noqa: F401
from forge.services import repo as _repo  # noqa: F401


def create_mcp() -> FastMCP:
    """Create the FastMCP server with service tools."""
    mcp = FastMCP("forge")
    expose_mcp(mcp)
    return mcp
