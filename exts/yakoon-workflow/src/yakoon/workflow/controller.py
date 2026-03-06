from __future__ import annotations

from collections.abc import Sequence
from typing import TYPE_CHECKING

from yakoon.base.runtime.controllers import Controller
from yakoon.workflow.commands.cmdset import WorkflowCommands

if TYPE_CHECKING:
    from yakoon.base.runtime import CommandSet


class WorkflowController(Controller):

    id: str = "workflow"
    is_listed: bool = False
    is_activatable: bool = False

    @property
    def commandsets(self) -> Sequence[type[CommandSet]]:
        return (WorkflowCommands,)
