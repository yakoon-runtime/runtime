from __future__ import annotations

from collections.abc import Sequence

from yakoon.base.runtime.commands import Command, CommandSet, Request
from yakoon.base.runtime.controllers import Controller, ResourceReferences
from yakoon.base.runtime.sessions import CommandSession

from .commands.core.cmdset import ShellSystemCommands


class ShellCoreController(Controller):
    """Core shell controller.

    This controller provides the default interactive shell environment:
      - system commands (help/man/exit, etc.)
      - workflow commands (wf.*)
      - templates and workflows rooted in yakoon.shell:core
    """

    id: str = "shell"
    is_shell: bool = True
    is_listed: bool = True
    is_activatable: bool = True

    resources = ResourceReferences(
        package="yakoon.shell",
    )

    @property
    def commandsets(self) -> Sequence[type[CommandSet]]:
        """Command sets exported by the shell controller."""
        return (ShellSystemCommands,)

    async def on_before_run_command(
        self, session: CommandSession, request: Request, command: Command
    ) -> None:
        """Touch session before executing any command.

        Notes:
            Keeping this in the controller makes the behavior consistent across all
            shell commands (system and workflow), without duplicating it in each
            command.
        """
        session.touch()
