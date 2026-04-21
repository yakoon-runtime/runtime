from __future__ import annotations

from yakoon.base.controllers import Controller, ResourceReferences

from ..commands import AuthSystemCommands


class AuthCoreController(Controller):
    """Authentication controller.

    Provides:
        - System-level authentication commands
        - Templates under yakoon.auth:core
    """

    id: str = "auth"

    is_shell: bool = False
    is_listed: bool = True
    is_activatable: bool = True

    commandsets = (AuthSystemCommands,)

    resources = ResourceReferences(
        package="yakoon.platform.capabilities.identity",
    )
