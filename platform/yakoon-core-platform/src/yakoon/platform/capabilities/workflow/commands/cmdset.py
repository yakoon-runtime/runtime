from collections.abc import Sequence

from yakoon.base.commands import Command, CommandSet

from .cmd_cancel import CmdWfCancel
from .cmd_input import CmdWfInput
from .cmd_next import CmdWfNext
from .cmd_run import CmdWfRun


class WorkflowCommands(CommandSet):

    group = "workflow"

    @classmethod
    def commands(cls) -> Sequence[type[Command]]:
        return [
            CmdWfRun,
            CmdWfInput,
            CmdWfNext,
            CmdWfCancel,
        ]
