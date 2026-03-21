"""1Password secret management for forge.

Provides helpers for managing secrets in 1Password, exposed
through the service layer as CLI commands and MCP tools.
"""

from __future__ import annotations

from click_clop.secrets import (
    SecretField,
    check_op_available,
    create_secret,
    delete_secret,
    ensure_secret,
    get_secret,
    get_secret_field,
)


def status() -> str:
    """Check if 1Password CLI is available and authenticated."""
    if check_op_available():
        return "1Password CLI is available and authenticated"
    return "1Password CLI is not available or not authenticated"


def get(vault: str, title: str, field: str = "") -> str:
    """Get a secret from 1Password.

    If field is specified, returns just that field value.
    Otherwise returns the full item as JSON.
    """
    import json

    if field:
        return get_secret_field(vault, title, field)
    item = get_secret(vault, title)
    return json.dumps(item, indent=2)


def create(vault: str, title: str, key: str, value: str) -> str:
    """Create a new secret in 1Password."""
    import json

    fields = [SecretField(label=key, value=value)]
    item = create_secret(vault, title, fields)
    return json.dumps(item, indent=2)


def ensure(vault: str, title: str, key: str, value: str) -> str:
    """Create or update a secret in 1Password (idempotent)."""
    import json

    fields = [SecretField(label=key, value=value)]
    item = ensure_secret(vault, title, fields)
    return json.dumps(item, indent=2)


def remove(vault: str, title: str) -> str:
    """Delete a secret from 1Password."""
    delete_secret(vault, title)
    return f"Deleted '{title}' from vault '{vault}'"
