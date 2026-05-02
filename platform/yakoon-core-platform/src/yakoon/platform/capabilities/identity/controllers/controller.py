from __future__ import annotations

from yakoon.base.controllers import Controller, ResourceReferences

from ..commands import BaseCommands


class BaseController(Controller):
    """Authentication controller.

    Provides:
        - System-level authentication commands
        - Templates under yakoon.auth:core
    """

    id: str = "id-base"

    commandsets = (BaseCommands,)

    resources = ResourceReferences(
        package="yakoon.platform.capabilities.identity",
    )
