from __future__ import annotations

from collections.abc import Sequence
from typing import TYPE_CHECKING

from yakoon.base.controllers.base import BaseController
from yakoon.workflow.commands.cmdset import WorkflowCommands

if TYPE_CHECKING:
    from yakoon.base.commands.commandset import CommandSet


class WorkflowController(BaseController):

    id: str = "workflow"
    is_listed: bool = False
    is_activatable: bool = False

    @property
    def commandsets(self) -> Sequence[type[CommandSet]]:
        return (WorkflowCommands,)
