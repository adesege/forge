"""Behave environment setup."""

# Import service modules to ensure they are loaded before any feature runs.
from forge.services import (  # noqa: F401
    auth,
    completion,
    issue,
    org,
    pr,
    release,
    repo,
)
