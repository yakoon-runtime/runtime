from yakoon.base.commands import CommandSet

from .cmd_cancel import CmdWfCancel
from .cmd_input import CmdWfInput
from .cmd_next import CmdWfNext
from .cmd_run import CmdWfRun


class WorkflowCommands(CommandSet):

    group = "workflow"

    commands = (
        CmdWfRun,
        CmdWfInput,
        CmdWfNext,
        CmdWfCancel,
    )
