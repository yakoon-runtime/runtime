from __future__ import annotations

from collections.abc import Sequence

from yakoon.base.commands.commandset import CommandSet
from yakoon.base.controllers.controller import Controller

from ..commands.cmdset import JobsCommands


class JobsController(Controller):

    id: str = "jobs"
    is_listed: bool = False
    is_activatable: bool = False

    @property
    def commandsets(self) -> Sequence[type[CommandSet]]:
        return (JobsCommands,)
