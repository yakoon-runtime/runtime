from __future__ import annotations

from collections.abc import Sequence

from yakoon.base.api import CommandSet
from yakoon.base.api.controller import Controller

from ..commands.cmdset import JobsCommands


class JobsController(Controller):

    id: str = "jobs"
    is_listed: bool = False
    is_activatable: bool = False

    @property
    def commandsets(self) -> Sequence[type[CommandSet]]:
        return (JobsCommands,)
