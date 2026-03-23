from __future__ import annotations

from collections.abc import Sequence
from typing import TYPE_CHECKING

from yakoon.base.runtime.controllers import Controller

from ..commands.cmdset import JobsCommands

if TYPE_CHECKING:
    from yakoon.base.runtime import CommandSet


class JobsController(Controller):

    id: str = "jobs"
    is_listed: bool = False
    is_activatable: bool = False

    @property
    def commandsets(self) -> Sequence[type[CommandSet]]:
        return (JobsCommands,)
