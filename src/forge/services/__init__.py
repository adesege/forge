"""Services for forge.

Each service module defines a Service subclass whose public methods
become CLI commands, MCP tools, and REST endpoints automatically.
"""

from forge.services import (
    auth,  # noqa: F401
    completion,  # noqa: F401
    install,  # noqa: F401
    issue,  # noqa: F401
    org,  # noqa: F401
    package,  # noqa: F401
    pr,  # noqa: F401
    release,  # noqa: F401
    repo,  # noqa: F401
)
