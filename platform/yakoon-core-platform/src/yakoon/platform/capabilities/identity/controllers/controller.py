from __future__ import annotations

from collections.abc import Sequence
from typing import TYPE_CHECKING

from yakoon.base.runtime.controllers import Controller
from yakoon.base.runtime.controllers.resources import ResourceReferences

from ..commands import AuthSystemCommands

if TYPE_CHECKING:
    from yakoon.base.runtime import CommandSet


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

    resources = ResourceReferences(
        package="yakoon.platform.capabilities.identity",
    )

    @property
    def commandsets(self) -> Sequence[type[CommandSet]]:
        """Command sets exported by this controller."""
        return (AuthSystemCommands,)
