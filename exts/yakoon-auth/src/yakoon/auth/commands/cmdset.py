from collections.abc import Sequence

from yakoon.auth.commands.cmd_su import CmdSu
from yakoon.auth.commands.cmd_whoami import CmdWhoAmI
from yakoon.base.runtime import Command, CommandSet


class AuthSystemCommands(CommandSet):

    group = "system"

    @classmethod
    def commands(cls) -> Sequence[type[Command]]:
        return [
            CmdSu,
            CmdWhoAmI,
        ]
