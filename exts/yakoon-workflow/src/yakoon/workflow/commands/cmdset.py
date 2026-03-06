from collections.abc import Sequence

from yakoon.base.runtime import Command, CommandSet
from yakoon.workflow.commands.cmd_cancel import CmdWfCancel
from yakoon.workflow.commands.cmd_input import CmdWfInput
from yakoon.workflow.commands.cmd_next import CmdWfNext
from yakoon.workflow.commands.cmd_run import CmdWfRun


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
