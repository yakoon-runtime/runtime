from collections.abc import Sequence

from yakoon.base.runtime import Command, CommandSet
from yakoon.shell.commands.core.cmd_exit import CmdExit
from yakoon.shell.commands.core.cmd_man import CmdMan
from yakoon.shell.commands.core.cmd_quit import CmdQuit
from yakoon.shell.commands.core.cmd_speed import CmdSpeedTest
from yakoon.shell.commands.core.cmd_su import CmdSu
from yakoon.shell.commands.core.cmd_test import CmdTest
from yakoon.shell.commands.core.cmd_use import CmdUse
from yakoon.shell.commands.core.cmd_version import CmdVersion
from yakoon.shell.commands.core.cmd_welcome import CmdWelcome


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
