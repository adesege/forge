"""Behave environment setup — ensure all services are registered."""

# Import all services so they auto-register before any feature runs
from forge.services import (
    auth,  # noqa: F401
    completion,  # noqa: F401
    issue,  # noqa: F401
    org,  # noqa: F401
    pr,  # noqa: F401
    release,  # noqa: F401
    repo,  # noqa: F401
)
