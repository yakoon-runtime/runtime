from __future__ import annotations

from yakoon.base.controllers.controller import Controller

from ..commands.cmdset import WorkflowCommands


class WorkflowController(Controller):

    id: str = "workflow"

    commandsets = (WorkflowCommands,)
