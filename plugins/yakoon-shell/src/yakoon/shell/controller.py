from __future__ import annotations

from yakoon.base.controllers import Controller, ResourceReferences

from .commands.core.cmdset import ShellSystemCommands


class ShellCoreController(Controller):

    id: str = "shell-core-controller"

    commandsets = (ShellSystemCommands,)

    resources = ResourceReferences(
        package="yakoon.shell",
    )
