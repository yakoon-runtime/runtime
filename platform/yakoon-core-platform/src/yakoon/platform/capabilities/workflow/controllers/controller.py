from __future__ import annotations

from yakoon.base.controllers import Composer

from ..commands.cmdset import WorkflowCommands


class WorkflowComposer(Composer):

    command_groups = (WorkflowCommands,)
