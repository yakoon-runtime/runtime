from __future__ import annotations

from yakoon.base.commands import Command, Request
from yakoon.base.controllers import Controller, ResourceReferences
from yakoon.base.runtime.sessions import Session

from .commands.core.cmdset import ShellSystemCommands


class ShellCoreController(Controller):
    """Core shell controller.

    This controller provides the default interactive shell environment:
      - system commands (help/man/exit, etc.)
      - workflow commands (wf.*)
      - templates and workflows rooted in yakoon.shell:core
    """

    id: str = "shell-core-controller"
    is_shell: bool = True
    is_listed: bool = True
    is_activatable: bool = True

    commandsets = (ShellSystemCommands,)

    resources = ResourceReferences(
        package="yakoon.shell",
    )

    async def on_before_run_command(
        self, session: Session, request: Request, command: Command
    ) -> None:
        """Touch session before executing any command.

        Notes:
            Keeping this in the controller makes the behavior consistent across all
            shell commands (system and workflow), without duplicating it in each
            command.
        """
        session.touch()  # type: ignore
