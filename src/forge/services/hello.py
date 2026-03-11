"""Example hello service — replace with your own services."""

from __future__ import annotations

from click_clop.service import Service


class HelloService(Service):
    """Greeting service with example methods."""

    name = "hello"
    description = "Greeting operations"

    def greet(self, name: str = "world") -> str:
        """Say hello to someone."""
        return f"Hello, {name}!"

    def farewell(self, name: str = "world") -> str:
        """Say goodbye to someone."""
        return f"Goodbye, {name}!"


# Auto-register on import
_service = HelloService()
