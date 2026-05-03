from yakoon.base.commands import CommandSet

from .cmd_exit import CmdExit
from .cmd_man import CmdMan
from .cmd_quit import CmdQuit
from .cmd_use import CmdUse
from .cmd_version import CmdVersion
from .cmd_welcome import CmdWelcome


class SystemCommands(CommandSet):

    group = "system"

    commands = (
        CmdQuit,
        CmdWelcome,
        CmdVersion,
        CmdUse,
        CmdExit,
        CmdMan,
    )
