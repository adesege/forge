"""Auth service — verify and manage Forgejo authentication."""

from __future__ import annotations

from click_clop.service import Service

from forge.forgejo import get_client
from forge.forgejo.formatting import format_user


class AuthService(Service):
    """Forgejo authentication operations."""

    name = "auth"
    description = "Manage Forgejo authentication"

    def status(self) -> str:
        """Check authentication status and display the logged-in user."""
        client = get_client()
        user = client.get("/user")
        return format_user(user)

    def token(self) -> str:
        """Display the configured API token (masked)."""
        import os

        from forge.config import load_config

        config = load_config(app_name="forge")
        forgejo_cfg = config.get("forgejo", {})

        token = os.environ.get("FORGE_FORGEJO__TOKEN", forgejo_cfg.get("token", ""))
        source = "environment variable" if os.environ.get("FORGE_FORGEJO__TOKEN") else "config file"

        if not token:
            op_ref = forgejo_cfg.get("token_op_ref", "")
            if op_ref:
                source = f"1Password ({op_ref})"
                token = "****"  # Don't resolve op here, just indicate it's configured

        if not token:
            return "No token configured."

        masked = "****" + token[-4:] if len(token) > 4 else "****"
        return f"Token: {masked}  (source: {source})"


_service = AuthService()
