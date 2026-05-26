from __future__ import annotations

from y5n.base.controllers import Composer

from ..commands.cmdset import WorkflowCommands


class WorkflowComposer(Composer):

    command_groups = (WorkflowCommands,)
