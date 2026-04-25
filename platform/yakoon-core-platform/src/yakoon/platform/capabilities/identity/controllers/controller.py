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

    commandsets = (AuthSystemCommands,)

    resources = ResourceReferences(
        package="yakoon.platform.capabilities.identity",
    )
