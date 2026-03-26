from __future__ import annotations

from collections.abc import Sequence

from yakoon.base.runtime.commands.commandset import CommandSet
from yakoon.base.runtime.controllers.controller import Controller

from ..commands.cmdset import WorkflowCommands


class WorkflowController(Controller):

    id: str = "workflow"
    is_listed: bool = False
    is_activatable: bool = False

    @property
    def commandsets(self) -> Sequence[type[CommandSet]]:
        return (WorkflowCommands,)
