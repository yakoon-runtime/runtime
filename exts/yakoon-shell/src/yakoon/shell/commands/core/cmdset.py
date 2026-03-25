from collections.abc import Sequence

from yakoon.base.api import Command, CommandSet

from .cmd_exit import CmdExit
from .cmd_man import CmdMan
from .cmd_quit import CmdQuit
from .cmd_speed import CmdSpeedTest
from .cmd_su import CmdSu
from .cmd_test import CmdTest
from .cmd_use import CmdUse
from .cmd_version import CmdVersion
from .cmd_welcome import CmdWelcome


class ShellSystemCommands(CommandSet):

    group = "system"

    @classmethod
    def commands(cls) -> Sequence[type[Command]]:
        return [
            CmdQuit,
            CmdWelcome,
            CmdVersion,
            CmdUse,
            CmdExit,
            CmdMan,
            CmdSu,
            CmdTest,
            CmdSpeedTest,
        ]
