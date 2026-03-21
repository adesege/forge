"""Behave environment setup."""

# Import all services so they auto-register before any feature runs
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


def before_all(context):
    """Start Forgejo container only for @integration scenarios."""
    context.forgejo = None
    # Only start if integration scenarios will actually run
    if _will_run_integration(context):
        from features.forgejo_fixture import start_forgejo

        context.forgejo = start_forgejo()


def after_all(context):
    """Stop the Forgejo container."""
    if getattr(context, "forgejo", None) is not None:
        context.forgejo.stop()


def _will_run_integration(context):
    """Check whether @integration scenarios will be executed."""
    tag_expression = getattr(context.config, "tags", None)
    if not tag_expression:
        # No tag filter — check if any feature file has @integration
        return False
    tag_str = str(tag_expression)
    # If explicitly requesting integration (e.g. --tags=integration)
    if tag_str == "integration" or tag_str == "@integration":
        return True
    # If excluding integration (e.g. --tags="~@integration" or --tags="not @integration")
    if "~" in tag_str or "not" in tag_str.lower():
        return False
    # Ambiguous — only start if "integration" appears positively
    return "integration" in tag_str
