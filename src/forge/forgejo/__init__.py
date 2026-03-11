"""Forgejo API client package."""

from __future__ import annotations

from forge.forgejo.client import ForgejoClient, get_client, reset_client
from forge.forgejo.exceptions import (
    ForgejoAPIError,
    ForgejoAuthError,
    ForgejoNotFoundError,
    ForgejoValidationError,
)

__all__ = [
    "ForgejoAPIError",
    "ForgejoAuthError",
    "ForgejoClient",
    "ForgejoNotFoundError",
    "ForgejoValidationError",
    "get_client",
    "reset_client",
]
