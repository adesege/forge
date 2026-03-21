"""Completion service — generate shell completion scripts."""

from __future__ import annotations

from click.shell_completion import BashComplete, FishComplete, ZshComplete

_PROG_NAME = "forge"
_COMPLETE_VAR = "_FORGE_COMPLETE"
_COMPLETE_FUNC = "_forge_completion"

_TEMPLATE_VARS = {
    "prog_name": _PROG_NAME,
    "complete_var": _COMPLETE_VAR,
    "complete_func": _COMPLETE_FUNC,
}


def bash() -> str:
    """Generate bash completion script. Eval with: eval "$(forge completion bash)"."""
    return BashComplete.source_template % _TEMPLATE_VARS


def zsh() -> str:
    """Generate zsh completion script. Eval with: eval "$(forge completion zsh)"."""
    return ZshComplete.source_template % _TEMPLATE_VARS


def fish() -> str:
    """Generate fish completion script. Pipe to: forge completion fish | source."""
    return FishComplete.source_template % _TEMPLATE_VARS
